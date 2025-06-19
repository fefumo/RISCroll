import codecs
from enum import auto
import struct
from typing import Dict, List, Tuple
from isa import INSTRUCTION_SET, ALIAS_REGISTERS
import sys

for i in range(32):
    ALIAS_REGISTERS[f"r{i}"] = i


def reg_to_num(reg):
    return ALIAS_REGISTERS[reg.strip(",")]


def to_bytes_data(data_code: List[Tuple[int, str, int]]) -> bytes:
    binary_bytes = bytearray()

    for _, line, val in data_code:
        if line.startswith(".byte"):
            binary_bytes.append(val & 0xFF)
        elif line.startswith(".word"):
            binary_bytes.extend(
                [val & 0xFF, (val >> 8) & 0xFF, (val >> 16) & 0xFF, (val >> 24) & 0xFF]
            )
        else:
            raise ValueError(f"Unsupported line format: {line}")

    return bytes(binary_bytes)


def to_bytes_text(text_code: List[int], entry_point: int) -> bytes:
    binary_bytes = bytearray()
    binary_bytes.extend(entry_point.to_bytes(4, "little"))
    for instr in text_code:
        binary_bytes.extend(
            [
                instr & 0xFF,
                (instr >> 8) & 0xFF,
                (instr >> 16) & 0xFF,
                (instr >> 24) & 0xFF,
            ]
        )
    return bytes(binary_bytes)


def to_hex(code: List[int], debug_info: List[Tuple[int, str, int]]) -> str:
    result = []
    for (addr, mnemonic, _), word in zip(debug_info, code):
        hex_word = f"{word:08X}"
        bin_word = f"{word:032b}"
        result.append(f"{addr:08X}(int {addr}) - {hex_word} - {bin_word} - {mnemonic}")
    return "\n".join(result)


def first_pass(
    lines: List[str],
) -> Tuple[Dict[str, int], List[Tuple[int, str]], List[Tuple[int, str]]]:
    """
    - Resolve labels and their addresses
    - Split into .text and .data sections
    - Track .org directives
    """
    addr_of_instr = 0
    label_map = {}
    section = None
    org = {".text": 0x0, ".data": 0x0}
    data_segment = []
    text_segment = []

    for line in lines:
        line = line.split("#")[0].strip()  # remove comments
        if not line:
            continue

        if line.startswith(".org"):
            _, addr = line.split()
            addr_of_instr = int(addr, 0)
            org[section] = addr_of_instr  # update current section address
            continue

        if line in [".text", ".data"]:
            section = line
            addr_of_instr = org[section]  # reset addr to .org
            continue

        if ":" in line:
            label, rest = line.split(":", 1)
            label = label.strip()
            label_map[label] = addr_of_instr  # store label address
            line = rest.strip()
            if not line:
                continue

        if section == ".data":
            if line.startswith(".word"):
                _, val = line.split(None, 1)
                data_segment.append((addr_of_instr, f".word {val.strip()}"))
                addr_of_instr += 4
            elif line.startswith(".byte"):
                _, val = line.split(None, 1)
                val = val.strip().strip("'\"")
                decoded = codecs.decode(val.encode("utf-8"), "unicode_escape")
                for c in decoded:
                    data_segment.append((addr_of_instr, f".byte {ord(c)}"))
                    addr_of_instr += 1

        elif section == ".text":
            text_segment.append((addr_of_instr, line))
            addr_of_instr += 4

    return label_map, data_segment, text_segment


def second_pass(
    instructions: List[Tuple[int, str]], label_map: Dict[str, int]
) -> Tuple[List[int], List[Tuple[int, str, int]]]:
    """
    Convert instructions and data to machine code.

    Returns:
        - list of binary instructions/data
        - debug info (address, source, encoded value)
    """
    code = []
    debug_info = []
    for addr_of_instr, line in instructions:
        if line.startswith(".word"):
            val = int(line.split()[1], 0)
            code.append(val & 0xFFFFFFFF)
            debug_info.append((addr_of_instr, line, val))
        elif line.startswith(".byte"):
            val = int(line.split()[1], 0)
            code.append(val)
            debug_info.append((addr_of_instr, line, val))
        else:
            instr = parse_line(line)
            binary = encode(instr, label_map, addr_of_instr)
            code.append(binary)
            debug_info.append((addr_of_instr, line, binary))
    return code, debug_info


def parse_line(line: str):
    parts = line.strip().split()
    instr = parts[0]
    operands = parts[1:] if len(parts) > 1 else []
    return (instr, operands)


# TODO: check if .get() with default value is ok or not
def get_token(
    operand: str, label_map: Dict[str, int], pc: int = 0, relative: bool = False
) -> int:
    """
    Converts an operand into a numeric value.

    Supported operand types:
    - 'low(label)'  — returns the lower 12 bits of the label's address.
    - 'high(label)' — returns the upper 20 bits (address rounded down to nearest 4KB).
    - 'label'       — returns the label's absolute address or offset from `pc` if `relative` is True.
    - numeric literal — returns the literal directly (supports decimal and hex, e.g., '123', '0x100').

    Args:
        operand: A string representing the operand (label, low/high(...) or literal).
        label_map: A dictionary mapping label names to their resolved addresses.
        pc: Current program counter; used for calculating relative addresses.
        relative: If True, returns the offset (label - pc) instead of the absolute address.

    Returns:
        An integer representing the resolved value of the operand.
    """
    operand = operand.strip(",")
    if operand.startswith("low("):
        label = operand[4:-1]
        return label_map.get(label, 0) & 0xFFF
    elif operand.startswith("high("):
        label = operand[5:-1]
        return label_map.get(label, 0) & 0xFFFFF000
    elif operand in label_map:
        val = label_map[operand]
        return val - pc if relative else val
    return int(operand, 0)


def twos_complement(value, bits):
    """
    Used for relative jumps (B-type) that can have a negative offset.
        twos_complement(+4, 12) -> 4 # 0b000000000100
        twos_complement(-4, 12) -> 4092 #0b111111111100
        twos_complement(-1, 13) -> 8191 # 0b1111111111111

    This is necessary to correctly represent negative values.
    in a fixed number of bits (for example, for B- and J-type instructions).
    """
    if value < 0:
        value = (1 << bits) + value
    return value


# TODO: write comms in `return` section of types
def encode(parsed, label_map: Dict[str, int], addr_of_instr: int) -> int:
    instr, operands = parsed
    info = INSTRUCTION_SET[instr]
    opcode = info["opcode"]
    typ = info["type"]

    if typ == "R":
        rd, rs1, rs2 = [reg_to_num(r) for r in operands]
        return (
            (info["funct7"] << 25)
            | (rs2 << 20)
            | (rs1 << 15)
            | (info["funct3"] << 12)
            | (rd << 7)
            | opcode
        )

    elif typ == "I":
        rd = reg_to_num(operands[0])
        if "(" in operands[1]:
            # lw t0, 0(t0)
            offset, rs1_str = operands[1].split("(")
            rs1 = reg_to_num(rs1_str.rstrip(")"))
            imm = get_token(offset, label_map)
        else:
            rs1 = reg_to_num(operands[1])
            imm = get_token(operands[2], label_map)
        return (
            ((imm & 0xFFF) << 20)
            | (rs1 << 15)
            | (info["funct3"] << 12)
            | (rd << 7)
            | opcode
        )

    elif typ == "S":
        rs2 = reg_to_num(operands[0])
        offset, rs1 = operands[1].split("(")
        rs1 = reg_to_num(rs1.rstrip(")"))
        imm = get_token(offset, label_map)
        imm11_5 = (imm >> 5) & 0x7F
        imm4_0 = imm & 0x1F
        return (
            (imm11_5 << 25)
            | (rs2 << 20)
            | (rs1 << 15)
            | (info["funct3"] << 12)
            | (imm4_0 << 7)
            | opcode
        )

    elif typ == "B":
        rs1 = reg_to_num(operands[0])
        rs2 = reg_to_num(operands[1])
        offset = get_token(operands[2], label_map, addr_of_instr, relative=True)

        assert offset % 2 == 0, "B-type offset must be 2-byte aligned"
        imm = twos_complement(offset, 13)  # 13 bit for sign + 12 for val

        imm_11 = (imm >> 11) & 0x1  # bit 7
        imm_4_1 = (imm >> 1) & 0xF  # bits 8–11
        imm_10_5 = (imm >> 5) & 0x3F  # bits 25–30
        imm_12 = (imm >> 12) & 0x1  # bit 31

        return (
            (imm_12 << 31)
            | (imm_10_5 << 25)
            | (rs2 << 20)
            | (rs1 << 15)
            | (info["funct3"] << 12)
            | (imm_4_1 << 8)
            | (imm_11 << 7)
            | opcode
        )

    elif typ == "U":
        rd = reg_to_num(operands[0])
        imm = get_token(operands[1], label_map)
        return (imm & 0xFFFFF000) | (rd << 7) | opcode

    elif typ == "J":
        rd = reg_to_num(operands[0])
        offset = get_token(operands[1], label_map, addr_of_instr, relative=True)
        imm = twos_complement(offset, 21)
        imm_20 = (imm >> 20) & 0x1
        imm_10_1 = (imm >> 1) & 0x3FF
        imm_11 = (imm >> 11) & 0x1
        imm_19_12 = (imm >> 12) & 0xFF
        return (
            (imm_20 << 31)
            | (imm_10_1 << 21)
            | (imm_11 << 20)
            | (imm_19_12 << 12)
            | (rd << 7)
            | opcode
        )

    elif typ == "SYS":
        return opcode  # opcode is already 0x7F for `halt`

    else:
        raise NotImplementedError(f"Unsupported instruction type: {typ}")


def dump_bin_as_text(bin_path: str):
    with open(bin_path, "rb") as f:
        content = f.read()
        words = struct.iter_unpack("<I", content)
        lines = []

        for i, (word,) in enumerate(words):
            addr = i * 4
            lines.append(f"{addr:08X} - {word:08X} - {word:032b}")

    out_path = "out/binary_decode.txt"

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def write_binaries(text_code, data_code, text_debug, data_debug, target_path):

    # TODO: it has to be data_code even tho data_debug is actually correct here. think of better naming or smth
    with open(target_path + ".data.bin", "wb") as f:
        f.write(to_bytes_data(data_debug))

    with open(target_path + ".text.log", "w", encoding="utf-8") as f:
        f.write(to_hex(text_code, text_debug))

    with open(target_path + ".data.log", "w", encoding="utf-8") as f:
        f.write(to_hex(data_code, data_debug))


def main(source_path, target_path):
    """create .bin file and debugging info"""

    target_path = target_path

    with open(source_path, encoding="utf-8") as f:
        source = f.read()

    lines = source.splitlines()
    label_map, data_segment, text_segment = first_pass(lines)
    text_segment_start_address = text_segment[0][0]
    data_code, data_debug = second_pass(data_segment, label_map)
    text_code, text_debug = second_pass(text_segment, label_map)

    # a little messy, but i have to do it since i gotta put initial text segment addr
    with open(target_path + ".text.bin", "wb") as f:
        f.write(to_bytes_text(text_code, text_segment_start_address))

    write_binaries(text_code, data_code, text_debug, data_debug, target_path)
    print(".text and .data binaries generated.")


if __name__ == "__main__":
    assert (
        len(sys.argv) == 3
    ), "Wrong arguments: translator.py <input_file> <target_file>"
    _, source, target = sys.argv
    main(source, target)
