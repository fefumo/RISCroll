from typing import Tuple
from machine.microcode import MicroInstruction, MicrocodeROM
from machine.logger import Logger


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
        self.logger = Logger(self)

    def load_input_file(self, filename, as_words=False):
        """
        Loads input data into the input buffer.

        If as_words is False, reads the file as raw bytes (byte-by-byte).
        If as_words is True, treats the file as a text file with one integer per line,
        and parses each line into a 32-bit signed integer.
        """

        with open(filename, "rb") as f:
            data = f.read()

        if as_words:
            with open(filename, "r") as f:
                lines = f.readlines()

            try:
                self.input_buffer = [
                    int(line.strip()) for line in lines if line.strip() != ""
                ]
            except ValueError as e:
                raise ValueError(f"Invalid number in input file: {e}")

        else:
            with open(filename, "rb") as f:
                data = f.read()
            if not data.endswith(b"\x00"):
                data += b"\x00"
            self.input_buffer = list(data)

    # TODO: `step` and `tick` should be renamed or be the same for easier understanding
    def step(self):
        microinstr = self.microcode_rom[self.mpc]
        self.logger.log()
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
            rd = (cpu.ir >> 7) & 0x1F
            addr = cpu.alu_out
            funct3 = (cpu.ir >> 12) & 0x7

            if addr == 0x1:
                value = cpu.input_buffer.pop(0) if cpu.input_buffer else 0

            else:
                if funct3 == 0b000:  # lw
                    value = int.from_bytes(cpu.data_mem[addr : addr + 4], "little")
                elif funct3 == 0b001:  # lb
                    value = cpu.data_mem[addr]
                    if value & 0x80:  # sign-extend
                        value |= -1 << 8
                else:
                    raise ValueError(f"Unsupported funct3 for mem_read: {funct3:03b}")

            cpu.registers[rd] = value & 0xFFFFFFFF

        # FIXME: solve the output buffer at 0x2 hardcoded problem
        if mi.mem_write:
            addr = cpu.alu_out
            val = cpu.registers[(cpu.ir >> 20) & 0x1F]  # rs2

            # TODO: clean-up code. too much branching. works for now tho
            # sb
            if mi.store_byte:
                val &= 0xFF
                if addr == 0x2:
                    cpu.output_buffer.append(chr(val))  # Output character
                else:
                    cpu.data_mem[addr] = val
            # sw
            else:
                if addr == 0x2:
                    cpu.output_buffer.append(int(val))
                else:
                    cpu.data_mem[addr : addr + 4] = val.to_bytes(4, "little")

        # Register write back
        if mi.latch_reg == "rd":
            rd = (cpu.ir >> 7) & 0x1F  # rd = instr[11..7]
            # if rd == 0 then the register isnt used. for example, in jal command
            # jal r0, <label> essentialy works as goto <label>
            if rd != 0:
                cpu.registers[rd] = cpu.alu_out

        if mi.latch_reg == "rd_pc":
            rd = (cpu.ir >> 7) & 0x1F  # rd in i-type. cringe but works for jalr
            if rd != 0:
                cpu.registers[rd] = cpu.pc

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

    elif opcode in (0x13, 0x03):  # I-type: addi, lw, jalr
        return extract_operands_i(cpu, ir)
    elif opcode == 0x67:  # jalr
        cpu.pc -= 4  # to work with current pc
        return extract_operands_i(cpu, ir)

    elif opcode == 0x23:  # S-type: sw
        return extract_operands_s(cpu, ir)

    elif opcode == 0x63:  # B-type: beq, etc.
        first, second, imm = extract_operands_b(cpu, ir)
        # cpu.pc -= 4  # to work with current pc
        if mi.latch_alu == "branch_offset":
            return (
                cpu.pc - 4,
                imm,
            )  # pc -4 cuz at this point, pc points to the NEXT instruction, not current. OMFG I LOST 10+ HOURS ON THIG BUG BRO
        else:
            return first, second

    elif opcode == 0x6F:  # J-type: jal
        # cpu.pc -= 4  # to work with current pc (cur pc is incremented after FETCH phase)
        if mi.latch_alu == "jal_link":
            return cpu.pc - 4, 4
        elif mi.latch_alu == "jal_offset":
            return extract_operands_j(cpu, ir)

    elif opcode == 0x37:  # U-type: lui
        return extract_operands_u(cpu, ir)

    raise ValueError(f"Unsupported opcode {opcode:#x} in extract_operands")


def extract_operands_r(cpu: CPU, ir: int) -> Tuple[int, int]:
    rs1 = (ir >> 15) & 0x1F
    rs2 = (ir >> 20) & 0x1F
    return cpu.registers[rs1], cpu.registers[rs2]


# def extract_regs_i(cpu: CPU, ir: int) -> Tuple[int, int]:
#     rd = (ir >> 7) & 0x1F
#     rs1 = (ir >> 15) & 0x1F
#     return cpu.registers[rs1], rd


def extract_operands_i(cpu: CPU, ir: int) -> Tuple[int, int]:
    rs1 = (ir >> 15) & 0x1F
    imm = (ir >> 20) & 0xFFF
    if imm & 0x800:
        imm |= -1 << 12  # sign-extend 12-bit immediate
    rs1_val = cpu.registers[rs1]
    return rs1_val, imm


def extract_operands_s(cpu: CPU, ir: int) -> Tuple[int, int]:
    rs1 = (ir >> 15) & 0x1F
    # rs2 = (ir >> 20) & 0x1F
    imm_11_5 = (ir >> 25) & 0x7F
    imm_4_0 = (ir >> 7) & 0x1F
    imm = (imm_11_5 << 5) | imm_4_0
    if imm & 0x800:
        imm |= -1 << 12  # sign-extend 12-bit immediate
    rs1_val = cpu.registers[rs1]
    return rs1_val, imm


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

    rs1_val = cpu.registers[rs1]
    rs2_val = cpu.registers[rs2]
    return rs1_val, rs2_val, imm


def extract_operands_u(cpu: CPU, ir: int) -> Tuple[int, int]:
    imm = ir & 0xFFFFF000
    return 0, imm


def extract_operands_j(cpu: CPU, ir: int) -> Tuple[int, int]:
    imm_20 = (ir >> 31) & 0x1
    imm_10_1 = (ir >> 21) & 0x3FF
    imm_11 = (ir >> 20) & 0x1
    imm_19_12 = (ir >> 12) & 0xFF

    imm = (imm_20 << 20) | (imm_19_12 << 12) | (imm_11 << 11) | (imm_10_1 << 1)

    # sign extend from bit 20 if negative
    if imm & (1 << 20):
        imm |= -1 << 21

    return cpu.pc - 4, imm


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
