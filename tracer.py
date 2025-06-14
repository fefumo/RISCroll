import json
import os

from machine.microcode import MicroInstruction

class Tracer:
    def __init__(self, cpu, log_dir="trace_output"):
        self.cpu = cpu
        self.tick_count = 0
        self.logs = []
        self.binary_trace = []
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        self.log_file = open(os.path.join(log_dir, "trace.log"), "w")
        self.bin_file = open(os.path.join(log_dir, "trace.json"), "w")

    def dump_registers(self):
        formatted_output = []
        for i in range(0, 32, 4):
            current_group = []
            for j in range(i, i + 4):
                current_group.append(f"r{j:02}={self.cpu.registers[j]:08X}")
            formatted_output.append(" ".join(current_group))
        return "\n".join(formatted_output)

    def dump_state(self):
        info = f"tick {self.tick_count}\n"
        info += f"PC = {self.cpu.pc:08X}\n"
        info += f"IR = {self.cpu.ir:08X}\n"
        info += f"MPC = {self.cpu.mpc}\n"
        info += f"ALU_OUT = {self.cpu.alu_out:08X}\n"
        info += f"FLAGS = Z:{self.cpu.flags['Z']} N:{self.cpu.flags['N']}\n"
        info += self.dump_registers() + "\n"
        self.log_file.write(info + "\n")
        self.logs.append(info)
        return info

    def trace_microinstr(self, mi: MicroInstruction):
        parts = [f"[µPC {self.cpu.mpc}] {mi.comment}"]
        if mi.latch_ir:
            parts.append("Fetching instruction...")
        if mi.latch_pc:
            parts.append(f"PC updated via: {mi.latch_pc}")
        if mi.latch_alu:
            parts.append(f"ALU operation: {mi.latch_alu}")
        if mi.mem_read:
            parts.append(f"Reading from memory at {self.cpu.alu_out:08X}")
        if mi.mem_write:
            parts.append(f"Writing to memory at {self.cpu.alu_out:08X}")
        if mi.latch_reg is not None:
            rd = (self.cpu.ir >> 7) & 0x1F
            parts.append(f"Result written to register r{rd}")


        trace_str = "\n".join(parts)
        self.log_file.write(trace_str + "\n")
        self.logs.append(trace_str)
        return trace_str

    def tick(self, mi):
        self.trace_microinstr(mi)
        self.dump_state()

        self.binary_trace.append({
            "tick": self.tick_count,
            "pc": self.cpu.pc,
            "ir": self.cpu.ir,
            "mpc": self.cpu.mpc,
            "alu_out": self.cpu.alu_out,
            "flags": self.cpu.flags.copy(),
            "registers": self.cpu.registers.copy()
        })
        self.tick_count += 1

    def finish(self):
        json.dump(self.binary_trace, self.bin_file, indent=2)
        self.log_file.close()
        self.bin_file.close()