"""Instruction Set Architecture of RISCroll."""

from typing import Literal, TypedDict


class InstructionProperties(TypedDict, total=False):
    type: Literal["R", "I", "S", "B", "U", "J", "SYS"]
    opcode: int
    funct3: int
    funct7: int


INSTRUCTION_SET: dict[str, InstructionProperties] = {
    "add": {"type": "R", "opcode": 0x33, "funct3": 0b000, "funct7": 0b0000000},
    "sub": {"type": "R", "opcode": 0x33, "funct3": 0b001, "funct7": 0b0000000},
    "and": {"type": "R", "opcode": 0x33, "funct3": 0b010, "funct7": 0b0000000},
    "or": {"type": "R", "opcode": 0x33, "funct3": 0b011, "funct7": 0b0000000},
    "xor": {"type": "R", "opcode": 0x33, "funct3": 0b100, "funct7": 0b0000000},
    "mul": {"type": "R", "opcode": 0x33, "funct3": 0b101, "funct7": 0b0000000},
    "div": {"type": "R", "opcode": 0x33, "funct3": 0b110, "funct7": 0b0000000},
    "lsl": {"type": "R", "opcode": 0x33, "funct3": 0b111, "funct7": 0b0000000},
    "lsr": {"type": "R", "opcode": 0x33, "funct3": 0b000, "funct7": 0b0000001},
    "addi": {"type": "I", "opcode": 0x13, "funct3": 0b000},
    "andi": {"type": "I", "opcode": 0x13, "funct3": 0b001},
    "ori": {"type": "I", "opcode": 0x13, "funct3": 0b010},
    "lw": {"type": "I", "opcode": 0x3, "funct3": 0b000},
    "lb": {"type": "I", "opcode": 0x3, "funct3": 0b001},
    "jalr": {"type": "I", "opcode": 0x67, "funct3": 0b000},
    "sw": {"type": "S", "opcode": 0x23, "funct3": 0b000},
    "sb": {"type": "S", "opcode": 0x23, "funct3": 0b001},
    "beq": {"type": "B", "opcode": 0x63, "funct3": 0b000},
    "bne": {"type": "B", "opcode": 0x63, "funct3": 0b001},
    "bgt": {"type": "B", "opcode": 0x63, "funct3": 0b010},
    "ble": {"type": "B", "opcode": 0x63, "funct3": 0b011},
    "lui": {"type": "U", "opcode": 0x37},
    "jal": {"type": "J", "opcode": 0x6F},
    "halt": {"type": "SYS", "opcode": 0x7F},
}

ALIAS_REGISTERS: dict[str, int] = {
    "zero": 0,
    "ra": 1,
    "sp": 2,
    "gp": 3,
    "tp": 4,
    "t0": 5,
    "t1": 6,
    "t2": 7,
    "s0": 8,
    "s1": 9,
    "a0": 10,
    "a1": 11,
    "a2": 12,
    "a3": 13,
    "a4": 14,
    "a5": 15,
    "a6": 16,
    "a7": 17,
    "s2": 18,
    "s3": 19,
    "s4": 20,
    "s5": 21,
    "s6": 22,
    "s7": 23,
    "t3": 24,
    "t4": 25,
    "t5": 26,
    "t6": 27,
    "x28": 28,
    "x29": 29,
    "x30": 30,
    "x31": 31,
}
