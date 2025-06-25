from dataclasses import dataclass

from machine.isa import INSTRUCTION_SET


@dataclass
class MicroInstruction:
    comment: str = ""
    latch_pc: str | None = None  # "inc", "alu", "branch"
    latch_ir: bool = False
    latch_reg: str | None = None  # register number (as string) or None
    latch_alu: str | None = None  # operation: add, sub, mul...
    latch_ar: str | None = None  # address in memory
    mem_read: bool = False
    mem_write: bool = False
    set_flags: bool = False
    next_mpc: int | None = None  # address of next microprogram
    jump_if: str | None = None  # condition (ZERO, NEG, ...)
    halt: bool = False
    store_byte: bool = False  # for differentiating between sb/sw


class MicrocodeROM:
    def __init__(self) -> None:
        self.code: dict[int, MicroInstruction] = {}
        self.decode_table: dict[tuple[int, int | None, int | None], int] = {}
        self.mpc_counter: int = 100

        self.fill_fetch()
        self.fill_from_isa()

    def __getitem__(self, mpc: int) -> MicroInstruction:
        """
        Allows you to access MicrocodeROM as a dictionary:
            rom = MicrocodeROM()
            instr = rom[42] # get the MicroInstruction at addr = 42

        If there is no instruction at the address mpc (error, empty slot, etc.),
        the instruction with a stop (halt) is returned.
        """
        return self.code.get(mpc, MicroInstruction(comment="HALT", halt=True))

    def fill_fetch(self) -> None:
        """
        Create the first 3 microinstructions that are executed for any instruction.
        This is a universal fetch-decode loop.
        """
        self.code[0] = MicroInstruction(
            comment="FETCH", latch_ir=True, latch_pc="inc", next_mpc=1000
        )
        # self.code[1] = MicroInstruction(comment="DECODE", next_mpc=1000) # look docs, i used to have instruction decder in scheme
        self.code[1000] = MicroInstruction(comment="DECODE DISPATCH", next_mpc=None)

    def register_decode(
        self,
        opcode: int,
        funct3: int | None = None,
        funct7: int | None = None,
        mpc: int | None = None,
    ) -> None:
        """
        Register a match: (opcode, funct3, funct7) -> mpc
        """
        key: tuple[int, int | None, int | None] = (opcode, funct3, funct7)
        if mpc is not None:
            self.decode_table[key] = mpc

    def get_decode_address(
        self, opcode: int, funct3: int | None = None, funct7: int | None = None
    ) -> int:
        """
        Try to find a suitable mpc address (start of firmware) for the instruction step by step:
            Exact match (opcode, funct3, funct7)
            If not found: ignore funct7 -> (opcode, funct3, None)
            If not found: ignore everything except opcode -> (opcode, None, None)
            If nothing found: return 9999 (HALT address)
        """
        result: int | None = (
            self.decode_table.get((opcode, funct3, funct7))
            or self.decode_table.get((opcode, funct3, None))
            or self.decode_table.get((opcode, None, None))
        )
        if result is None:
            raise ValueError(
                f"Unsupported instruction: opcode=0b{opcode:07b} (0x{opcode:02X}), "
                f"funct3={'-' if funct3 is None else f'0b{funct3:03b}'}, "
                f"funct7={'-' if funct7 is None else f'0b{funct7:07b}'}"
            )

        return result

    def alloc(self, count: int = 1) -> int:
        addr: int = self.mpc_counter
        self.mpc_counter += count
        return addr

    def fill_from_isa(self) -> None:
        for name, props in INSTRUCTION_SET.items():
            t: str = props["type"]
            op: str = name
            opcode: int = props["opcode"]
            funct3: int | None = props.get("funct3")
            funct7: int | None = props.get("funct7")

            if t == "R":
                addr: int = self.alloc(2)
                self.register_decode(opcode, funct3, funct7, addr)
                self.code[addr] = MicroInstruction(
                    comment=f"R-{op}", latch_alu=op, set_flags=True, next_mpc=addr + 1
                )
                self.code[addr + 1] = MicroInstruction(comment="WB", latch_reg="rd", next_mpc=0)

            elif t == "I":
                if op == "lw":
                    addr = self.alloc(2)
                    self.register_decode(opcode, funct3, None, addr)
                    self.code[addr] = MicroInstruction(
                        comment="I-LW addr", latch_alu="add", next_mpc=addr + 1
                    )
                    self.code[addr + 1] = MicroInstruction(
                        comment="I-LW load", mem_read=True, next_mpc=0
                    )
                elif op == "lb":
                    addr = self.alloc(2)
                    self.register_decode(opcode, funct3, None, addr)
                    self.code[addr] = MicroInstruction(
                        comment="I-LB addr", latch_alu="add", next_mpc=addr + 1
                    )
                    self.code[addr + 1] = MicroInstruction(
                        comment="I-LB load byte", mem_read=True, next_mpc=0
                    )
                elif op == "jalr":
                    addr = self.alloc(3)
                    self.register_decode(opcode, funct3, None, addr)
                    self.code[addr] = MicroInstruction(
                        comment="I-JALR save return address",
                        latch_reg="rd_pc",
                        next_mpc=addr + 1,
                    )
                    self.code[addr + 1] = MicroInstruction(
                        comment="I-JALR addr", latch_alu="add", next_mpc=addr + 2
                    )
                    self.code[addr + 2] = MicroInstruction(
                        comment="I-JALR jump", latch_pc="alu", next_mpc=0
                    )
                else:
                    addr = self.alloc(2)
                    self.register_decode(opcode, funct3, None, addr)
                    self.code[addr] = MicroInstruction(
                        comment=f"I-{op}",
                        latch_alu=op,
                        set_flags=True,
                        next_mpc=addr + 1,
                    )
                    self.code[addr + 1] = MicroInstruction(comment="WB", latch_reg="rd", next_mpc=0)

            elif t == "S":
                addr = self.alloc(2)
                self.register_decode(opcode, funct3, None, addr)
                self.code[addr] = MicroInstruction(
                    comment=f"S-{op} addr", latch_alu="add", next_mpc=addr + 1
                )
                if op == "sb":
                    self.code[addr + 1] = MicroInstruction(
                        comment=f"S-{op} store",
                        mem_write=True,
                        store_byte=True,
                        next_mpc=0,
                    )
                elif op == "sw":
                    self.code[addr + 1] = MicroInstruction(
                        comment=f"S-{op} store", mem_write=True, next_mpc=0
                    )

            elif t == "B":
                addr = self.alloc(3)
                cond_map: dict[str, str] = {"beq": "Z", "bne": "NZ", "bgt": "GT", "ble": "LE"}
                cond: str = cond_map[op]
                self.register_decode(opcode, funct3, None, addr)

                self.code[addr] = MicroInstruction(
                    comment=f"B-{op} cmp",
                    latch_alu="sub",
                    set_flags=True,
                    next_mpc=addr + 1,
                )
                self.code[addr + 1] = MicroInstruction(
                    comment=f"B-{op} offset",
                    latch_alu="branch_offset",
                    next_mpc=addr + 2,
                )
                self.code[addr + 2] = MicroInstruction(
                    comment="B-cond", latch_pc="branch", jump_if=cond, next_mpc=0
                )

            elif t == "U":
                addr = self.alloc(2)
                self.register_decode(opcode, None, None, addr)
                self.code[addr] = MicroInstruction(
                    comment="U-LUI", latch_alu="lui", next_mpc=addr + 1
                )
                self.code[addr + 1] = MicroInstruction(
                    comment="U-LUI write", latch_reg="rd", next_mpc=0
                )

            elif t == "J":
                addr = self.alloc(2)
                self.register_decode(opcode, None, None, addr)
                # save PC + 4
                self.code[addr] = MicroInstruction(
                    comment="J-JAL link",
                    latch_alu="jal_link",
                    latch_reg="rd",
                    next_mpc=addr + 1,
                )

                # perform jump
                self.code[addr + 1] = MicroInstruction(
                    comment="J-JAL jump",
                    latch_alu="jal_offset",
                    latch_pc="alu",
                    next_mpc=0,
                )

            elif t == "SYS":
                self.register_decode(opcode, None, None, 9999)
                self.code[9999] = MicroInstruction(comment="HALT", halt=True)
