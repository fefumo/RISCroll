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
        self.running = True

        # Load initial data memory
        self.data_mem[: len(data_mem)] = data_mem

        self.cu = ControlUnit()
        self.microcode_rom = MicrocodeROM()
        self.tracer = Tracer(self)

    def step(self):
        microinstr = self.microcode_rom[self.mpc]
        self.tracer.tick(microinstr)
        self.cu.execute(self, microinstr)


class ControlUnit:
    def execute(self, cpu: CPU, mi: MicroInstruction):
        if cpu.mpc == 1000:
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

        if mi.latch_pc == "inc":
            cpu.pc += 4
        elif mi.latch_pc == "alu":
            cpu.pc = cpu.alu_out
        elif mi.latch_pc == "branch":
            if should_jump(cpu, mi.jump_if):
                cpu.pc = cpu.alu_out

        if mi.latch_alu:
            a, b = extract_operands(cpu, mi)
            cpu.alu_out = ALU.exec(mi.latch_alu, a, b)

            if mi.set_flags:
                cpu.flags["Z"] = int(cpu.alu_out == 0)
                cpu.flags["N"] = int(cpu.alu_out < 0)

        if mi.mem_read:
            rd = (
                cpu.ir >> 7
            ) & 0x1F  # shift 7 to get rd (check isa), &0x1F to get rid of bits that are to the left
            addr = cpu.alu_out
            value = int.from_bytes(
                cpu.data_mem[addr : addr + 4], "little"
            )  # read whole word
            # print(f"[READ] addr=0x{addr:04X} -> t{rd} = 0x{value:08X}")
            cpu.registers[rd] = value

        if mi.mem_write:
            addr = cpu.alu_out
            val = cpu.registers[(cpu.ir >> 20) & 0x1F] & 0xFF  # rs2
            if addr == 0x2:
                cpu.output_buffer.append(chr(val))  # Output character
            else:
                cpu.data_mem[addr] = val

        # Register write back
        if isinstance(mi.latch_reg, str) and mi.latch_reg == "rd":
            rd = (cpu.ir >> 7) & 0x1F
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


# TODO: separate??
def extract_operands(cpu: CPU, mi: MicroInstruction):
    ir = cpu.ir
    rs1 = (ir >> 15) & 0x1F
    rs2 = (ir >> 20) & 0x1F
    imm_i = (ir >> 20) & 0xFFF
    if imm_i & 0x800:
        imm_i |= ~0xFFF  # Sign-extend

    opcode = ir & 0x7F

    if opcode == 0x13:
        return cpu.registers[rs1], imm_i
    elif opcode == 0x03:  # lw
        return cpu.registers[rs1], imm_i
    elif opcode == 0x23:  # sw
        imm_s = ((ir >> 25) << 5) | ((ir >> 7) & 0x1F)
        if imm_s & 0x800:
            imm_s |= ~0xFFF
        return cpu.registers[rs1], imm_s
    elif opcode == 0x33:  # R-type
        return cpu.registers[rs1], cpu.registers[rs2]
    elif opcode == 0x67:  # jalr
        return cpu.registers[rs1], imm_i
    elif opcode == 0x6F:  # jal
        imm_j = (
            ((ir >> 31) << 20)
            | (((ir >> 21) & 0x3FF) << 1)
            | (((ir >> 20) & 0x1) << 11)
            | (((ir >> 12) & 0xFF) << 12)
        )
        if imm_j & (1 << 20):
            imm_j |= ~((1 << 21) - 1)
        return cpu.pc, imm_j
    return 0, 0  # fallback


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
        if op == "jal":
            return a + b
        return 0
