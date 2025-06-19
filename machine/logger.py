import os


class Logger:
    def __init__(self, cpu, log_dir="log_output"):
        self.cpu = cpu
        self.last_pc = cpu.pc
        self.last_registers = cpu.registers.copy()

        os.makedirs(log_dir, exist_ok=True)
        self.log_file = open(os.path.join(log_dir, "trace.log"), "w")

    def _changed_registers(self):
        changes = []
        for i, (old, new) in enumerate(zip(self.last_registers, self.cpu.registers)):
            if old != new:
                changes.append(f"r{i}={new:08X}({new})")
        self.last_registers = self.cpu.registers.copy()
        return " ".join(changes)

    def log(self):
        if self.cpu.pc != self.last_pc:
            self._log_state()
            self.last_pc = self.cpu.pc

    def _log_state(self):
        reg_changes = self._changed_registers()
        line = (
            f"PC=0x{self.cpu.pc:08X}({self.cpu.pc}) "
            f"MPC={self.cpu.mpc} "
            f"NZ={self.cpu.flags['N']}{self.cpu.flags['Z']} "
            f"IR=0x{self.cpu.ir:08X}({self.cpu.ir}) "
            + reg_changes
        )
        self.log_file.write(line + "\n")

    def finish(self):
        self.log_file.close()
