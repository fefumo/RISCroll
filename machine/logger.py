"""Module for CPU logging and trace generation."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # for mypy
    from machine.machine import CPU

import os


class Logger:
    """Logs the state of the CPU at each step."""

    def __init__(self, cpu: CPU, log_dir: str = "log_output") -> None:
        """
        Initializes the Logger.

        Args:
            cpu: The CPU instance to monitor.
            log_dir: Directory to store log files.
        """
        self.cpu = cpu
        self.last_pc: int = cpu.pc
        self.last_registers: list[int] = cpu.registers.copy()

        os.makedirs(log_dir, exist_ok=True)
        self.log_file = open(os.path.join(log_dir, "trace.log"), "w") # noqa: SIM115

    def _changed_registers(self) -> str:
        """
        Compares current registers with the last logged state and returns a string
        describing changes.
        """
        changes: list[str] = []
        for i, (old, new) in enumerate(zip(self.last_registers, self.cpu.registers, strict=False)):
            if old != new:
                changes.append(f"r{i}={new:08X}({new})")
        self.last_registers = self.cpu.registers.copy()
        return " ".join(changes)

    def log(self) -> None:
        """Logs the CPU state if the Program Counter (PC) has changed."""
        if self.cpu.pc != self.last_pc:
            self._log_state()
            self.last_pc = self.cpu.pc

    def _log_state(self) -> None:
        """Writes the current CPU state to the log file."""
        reg_changes: str = self._changed_registers()
        line: str = (
            f"PC=0x{self.cpu.pc:08X}({self.cpu.pc}) "
            f"MPC={self.cpu.mpc} "
            f"NZ={self.cpu.flags['N']}{self.cpu.flags['Z']} "
            f"IR=0x{self.cpu.ir:08X}({self.cpu.ir}) " + reg_changes
        )
        self.log_file.write(line + "\n")

    def finish(self) -> None:
        """Closes the log file."""
        self.log_file.close()
