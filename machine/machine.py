from typing import Tuple
from machine.microcode import MicroInstruction, MicrocodeROM
from tracer import Tracer


class CPU:
    def __init__(self, instr_mem: bytes, data_mem: bytes):
        self.pc = 0
        self.ir = 0
        self.mpc = 0
        self.registers = [0] * 32
        self.data_mem = bytearray(1024 * 64)
        self.instr_mem = instr_mem
        self.alu_out = 0
        self.flags = {"Z": 0, "N": 0}
        self.output_buffer = []
        self.input_buffer = []
        self.running = True

        # Load initial data memory
        self.data_mem[: len(data_mem)] = data_mem

        self.cu = ControlUnit()
        self.microcode_rom = MicrocodeROM()
        self.tracer = Tracer(self)

    def load_input_file(self, filename):
        with open(filename, "rb") as f:
            data = f.read()
        
        # null terminate
        if not data.endswith(b'\x00'):
            data += b'\x00'
        
        self.input_buffer = list(data)

    def step(self):
        microinstr = self.microcode_rom[self.mpc]
        self.tracer.tick(microinstr)
        self.cu.execute(self, microinstr)


class ControlUnit:
    def execute(self, cpu: CPU, mi: MicroInstruction):
        if cpu.mpc == 1000:
            """======= DECODE DISPATCH ======="""
            # Dispatch to correct microprogram start address
            opcode = cpu.ir & 0x7F
            funct3 = (cpu.ir >> 12) & 0x7
            funct7 = (cpu.ir >> 25) & 0x7F
            mpc_new = cpu.microcode_rom.get_decode_address(opcode, funct3, funct7)
            cpu.mpc = mpc_new
            return

        if mi.halt:
            cpu.running = False
            return

        # Instruction Fetch
        if mi.latch_ir:
            word = int.from_bytes(cpu.instr_mem[cpu.pc : cpu.pc + 4], "little")
            cpu.ir = word

        # === ALU stage must happen before PC update ===
        if mi.latch_alu:
            a, b = extract_operands(cpu, mi)
            cpu.alu_out = ALU.exec(mi.latch_alu, a, b)

            if mi.set_flags:
                cpu.flags["Z"] = int(cpu.alu_out == 0)
                cpu.flags["N"] = int(cpu.alu_out < 0)

        if mi.latch_pc == "inc":
            cpu.pc += 4
        elif mi.latch_pc == "alu":
            cpu.pc = cpu.alu_out
        elif mi.latch_pc == "branch":
            if should_jump(cpu, mi.jump_if):
                cpu.pc = cpu.alu_out

        if mi.mem_read:
            rd = (
                cpu.ir >> 7
            ) & 0x1F  # shift 7 to get rd (check isa), &0x1F to get rid of bits that are to the left
            addr = cpu.alu_out
            value = int.from_bytes(
                cpu.data_mem[addr : addr + 4], "little"
            )  # read whole word
            # print(f"[READ] addr=0x{addr:04X} -> t{rd} = 0x{value:08X}")
            if addr == 0x1:
                if cpu.input_buffer:
                    value = cpu.input_buffer.pop(0)
                else:
                    value = 0  # EOF
            else:
                value = int.from_bytes(cpu.data_mem[addr : addr + 4], "little")
                
            cpu.registers[rd] = value

        # FIXME: solve the output buffer at 0x2 hardcoded problem
        if mi.mem_write:
            addr = cpu.alu_out
            # FIXME: it's sb, not sw at this point.
            val = cpu.registers[(cpu.ir >> 20) & 0x1F] & 0xFF  # rs2
            if addr == 0x2:
                cpu.output_buffer.append(chr(val))  # Output character
            else:
                cpu.data_mem[addr] = val

        # Register write back
        if isinstance(mi.latch_reg, str) and mi.latch_reg == "rd":
            rd = (cpu.ir >> 7) & 0x1F  # rd = instr[11..7]
            # if rd == 0 then the register isnt used. for example, in jal command
            # jal r0, <label> essentialy works as goto <label>
            if rd != 0:
                cpu.registers[rd] = cpu.alu_out
        elif mi.latch_reg is not None:
            cpu.registers[mi.latch_reg] = cpu.alu_out

        if mi.next_mpc is not None:
            cpu.mpc = mi.next_mpc


def should_jump(cpu: CPU, condition):
    match condition:
        case "Z":
            return cpu.flags["Z"] == 1
        case "NZ":
            return cpu.flags["Z"] == 0
        case "GT":
            return cpu.flags["N"] == 0 and cpu.flags["Z"] == 0
        case "LE":
            return cpu.flags["N"] == 1 or cpu.flags["Z"] == 1
        case _:
            return False


# that's tough man...
def extract_operands(cpu: CPU, mi: MicroInstruction):
    ir = cpu.ir
    opcode = ir & 0x7F

    if opcode == 0x33:
        return extract_operands_r(cpu, ir)

    elif opcode in (0x13, 0x03, 0x67):  # I-type: addi, lw, jalr
        return extract_operands_i(cpu, ir)

    elif opcode == 0x23:  # S-type: sw
        return extract_operands_s(cpu, ir)

    elif opcode == 0x63:  # B-type: beq, etc.
        first, second, imm = extract_operands_b(cpu, ir)
        if mi.latch_alu == "branch_offset":
            return cpu.pc - 4, imm# pc -4 cuz at this point, pc points to the NEXT instruction, not current. OMFG I LOST 5 HOURS ON THIG BUG BRO
        else:
            return first, second

    elif opcode == 0x6F:  # J-type: jal
        if mi.latch_alu == "jal_link":
            return cpu.pc, 4
        elif mi.latch_alu == "jal_offset":
            return extract_operands_j(cpu, ir)

    elif opcode == 0x37:  # U-type: lui
        return extract_operands_u(cpu, ir)

    raise ValueError(f"Unsupported opcode {opcode:#x} in extract_operands")


def extract_operands_r(cpu: CPU, ir: int) -> Tuple[int, int]:
    rs1 = (ir >> 15) & 0x1F
    rs2 = (ir >> 20) & 0x1F
    return cpu.registers[rs1], cpu.registers[rs2]


def extract_operands_i(cpu: CPU, ir: int) -> Tuple[int, int]:
    rs1 = (ir >> 15) & 0x1F
    imm = (ir >> 20) & 0xFFF
    if imm & 0x800:
        imm |= -1 << 12  # sign-extend 12-bit immediate
    return cpu.registers[rs1], imm


def extract_operands_s(cpu: CPU, ir: int) -> Tuple[int, int]:
    rs1 = (ir >> 15) & 0x1F
    #rs2 = (ir >> 20) & 0x1F
    imm_11_5 = (ir >> 25) & 0x7F
    imm_4_0 = (ir >> 7) & 0x1F
    imm = (imm_11_5 << 5) | imm_4_0
    if imm & 0x800:
        imm |= -1 << 12  # sign-extend 12-bit immediate
    return cpu.registers[rs1], imm


def extract_operands_b(cpu: CPU, ir: int) -> Tuple[int, int, int]:
    rs1 = (ir >> 15) & 0x1F
    rs2 = (ir >> 20) & 0x1F
    imm_12 = (ir >> 31) & 0x1
    imm_10_5 = (ir >> 25) & 0x3F
    imm_4_1 = (ir >> 8) & 0xF
    imm_11 = (ir >> 7) & 0x1

    imm = (imm_12 << 12) | (imm_11 << 11) | (imm_10_5 << 5) | (imm_4_1 << 1)
    if imm & 0x1000:
        imm |= -1 << 13  # sign-extend 13-bit immediate (imm[12] is sign bit)

    return cpu.registers[rs1], cpu.registers[rs2], imm


def extract_operands_u(cpu: CPU, ir: int) -> Tuple[int, int]:
    imm = ir & 0xFFFFF000
    return 0, imm


def extract_operands_j(cpu: CPU, ir: int) -> Tuple[int, int]:
    imm = (ir >> 12) & 0xFFFFF
    if imm & (1 << 19):
        imm |= -1 << 20  # sign-extend 20-bit immediate
    offset = imm << 12
    return cpu.pc, offset

class ALU:
    @staticmethod
    def exec(op, a, b):
        if op in {"add", "addi"}:
            return a + b
        if op in {"sub"}:
            return a - b
        if op in {"mul"}:
            return a * b
        if op in {"div"}:
            return a // b if b != 0 else 0
        if op in {"and", "andi"}:
            return a & b
        if op in {"or", "ori"}:
            return a | b
        if op in {"xor", "xori"}:
            return a ^ b
        if op in {"lsl"}:
            return a << b
        if op in {"lsr"}:
            return a >> b
        if op == "lui":
            return b << 12
        if op == "jal_link":  # PC + 4
            return a + b
        if op == "jal_offset":  # PC + offset
            return a + b
        if op == "branch_offset":
            return a + b  # a = pc, b = imm
        return 0
