from enum import auto
import struct
from typing import Dict, List, Tuple
from isa import INSTRUCTION_SET, ALIAS_REGISTERS
import sys

for i in range(32):
    ALIAS_REGISTERS[f"r{i}"] = i


def reg_to_num(reg):
    return ALIAS_REGISTERS[reg.strip(",")]


def to_bytes(code: List[int]):
    binary_bytes = bytearray()
    for instr in code:
        if isinstance(instr, int):
            binary_instr = instr
        else:
            raise ValueError("Unsupported instruction format")

        binary_bytes.extend(
            (
                (binary_instr >> 24) & 0xFF,
                (binary_instr >> 16) & 0xFF,
                (binary_instr >> 8) & 0xFF,
                binary_instr & 0xFF,
            )
        )
    return bytes(binary_bytes)


def to_hex(code: List[int], debug_info: List[Tuple[int, str, int]]) -> str:
    result = []
    for (addr, mnemonic, _), word in zip(debug_info, code):
        hex_word = f"{word:08X}"
        bin_word = f"{word:032b}"
        result.append(f"{addr:08X} - {hex_word} - {bin_word} - {mnemonic}")
    return "\n".join(result)


def translate(source: str):
    lines = source.splitlines()
    symbol_table, data_segment, text_segment = first_pass(lines)
    data_code, data_debug = second_pass(data_segment, symbol_table)
    text_code, text_debug = second_pass(text_segment, symbol_table)
    return data_code + text_code, data_debug + text_debug


def first_pass(
    lines: List[str],
) -> Tuple[Dict[str, int], List[Tuple[int, str]], List[Tuple[int, str]]]:
    addr_of_instr = 0
    symbol_table = {}
    section = None
    org = {".text": 0x0, ".data": 0x0}
    data_segment = []
    text_segment = []

    for line in lines:
        line = line.split("#")[0].strip()
        if not line:
            continue

        if line.startswith(".org"):
            _, addr = line.split()
            addr_of_instr = int(addr, 0)
            org[section] = addr_of_instr
            continue

        if line in [".text", ".data"]:
            section = line
            addr_of_instr = org[section]
            continue

        if ":" in line:
            label, rest = line.split(":", 1)
            label = label.strip()
            symbol_table[label] = addr_of_instr
            line = rest.strip()  # there is a part left with a directive or instruction

            if not line:
                continue  # if nothing left, go to the next line

        if section == ".data":
            if line.startswith(".word"):
                _, val = line.split(None, 1)
                # symbol_table[f'data_{addr_of_instr:08x}'] = addr_of_instr
                data_segment.append((addr_of_instr, f".word {val.strip()}"))
                addr_of_instr += 4
            elif line.startswith(".byte"):
                _, val = line.split(None, 1)
                val = val.strip().strip("'\"")
                for c in val:
                    # symbol_table[f'data_{addr_of_instr:08x}'] = addr_of_instr
                    data_segment.append((addr_of_instr, f".byte {ord(c)}"))
                    addr_of_instr += 1
        elif section == ".text":
            text_segment.append((addr_of_instr, line))
            addr_of_instr += 4

    return symbol_table, data_segment, text_segment


def second_pass(
    instructions: List[Tuple[int, str]], symbol_table: Dict[str, int]
) -> Tuple[List[int], List[Tuple[int, str, int]]]:
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
            binary = encode(instr, symbol_table, addr_of_instr)
            code.append(binary)
            debug_info.append((addr_of_instr, line, binary))
    return code, debug_info


def parse_line(line: str):
    parts = line.strip().split()
    instr = parts[0]
    operands = parts[1:] if len(parts) > 1 else []
    return (instr, operands)


def get_token(
    operand: str, symbol_table: Dict[str, int], pc: int = 0, relative: bool = False
) -> int:
    operand = operand.strip(",")
    if operand.startswith("low("):
        label = operand[4:-1]
        return symbol_table.get(label, 0) & 0xFFF
    elif operand.startswith("high("):
        label = operand[5:-1]
        return (symbol_table.get(label, 0) >> 12) << 12
    elif operand in symbol_table:
        val = symbol_table[operand]
        return val - pc if relative else val
    return int(operand, 0)


def encode(parsed, symbol_table: Dict[str, int], addr_of_instr: int) -> int:
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
            imm = get_token(offset, symbol_table)
        else:
            rs1 = reg_to_num(operands[1])
            imm = get_token(operands[2], symbol_table)

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
        imm = get_token(offset, symbol_table)
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
        offset = get_token(operands[2], symbol_table, addr_of_instr, relative=True)
        imm = offset & 0xFFF  # use lower 12 bits only
        return (
            (imm << 20)  # [31..20] = imm[11:0]
            | (rs2 << 15)  # [19..15]
            | (rs1 << 10)  # [14..10]
            | (info["funct3"] << 7)  # [9..7]
            | opcode  # [6..0]
        )

    elif typ == "U":
        rd = reg_to_num(operands[0])
        imm = get_token(operands[1], symbol_table)
        return (imm & 0xFFFFF000) | (rd << 7) | opcode

    elif typ == "J":
        rd = reg_to_num(operands[0])
        offset = get_token(operands[1], symbol_table, addr_of_instr, relative=True)
        imm = offset & 0xFFFFF000
        return (imm) | (rd << 7) | opcode

    elif typ == "SYS":
        return (0b1111111 << 25) | opcode

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


def main(source_path, target_path):
    """create .bin file and debugging info"""

    target_path = "out/" + target_path

    with open(source_path, encoding="utf-8") as f:
        source = f.read()

    code, debug_info = translate(source)

    with open(target_path + ".bin", "wb") as f:
        f.write(to_bytes(code))

    debug_output = to_hex(code, debug_info)
    with open(target_path + ".dbg.txt", "w", encoding="utf-8") as f:
        f.write(debug_output)

    print(
        "\n===== DEBUG INFO =====\n" + "format: \nAddr - hex_word - bin_word - mnemonic"
    )
    print(debug_output)

    dump_bin_as_text(target_path + ".bin")


if __name__ == "__main__":
    assert (
        len(sys.argv) == 3
    ), "Wrong arguments: translator.py <input_file> <target_file>"
    _, source, target = sys.argv
    main(source, target)
