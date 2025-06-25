# translator.py
import codecs
import re
import struct
import sys
from collections.abc import Sequence

from isa import ALIAS_REGISTERS, INSTRUCTION_SET

for i in range(32):
    ALIAS_REGISTERS[f"r{i}"] = i


def reg_to_num(reg):
    return ALIAS_REGISTERS[reg.strip(",")]


def to_bytes_data(data_debug: list[tuple[int, str, int]]) -> bytes:
    """
    Converts data segment debug information into a byte sequence.
    data_debug contains (address, source_line, value_to_encode).
    """
    binary_bytes = bytearray()

    for _, line_type, val in data_debug:
        if line_type.startswith(".byte"):
            binary_bytes.append(val & 0xFF)
        elif line_type.startswith(".word"):
            binary_bytes.extend(val.to_bytes(4, "little"))
        else:
            raise ValueError(f"Unsupported data line format: {line_type}")

    return bytes(binary_bytes)


def to_bytes_text(text_code: list[int], entry_point: int) -> bytes:
    binary_bytes = bytearray()
    binary_bytes.extend(entry_point.to_bytes(4, "little"))
    for instr in text_code:
        binary_bytes.extend(instr.to_bytes(4, "little"))
    return bytes(binary_bytes)


def to_hex(debug_info: list[tuple[int, str, int]]) -> str:
    """
    Generates a human-readable hexadecimal and binary representation
    of the machine code along with source mnemonics.
    debug_info: list of (address, source_mnemonic, encoded_value)
    """
    result = []
    for addr, mnemonic, word in debug_info:
        hex_word = f"{word:08X}"
        bin_word = f"{word:032b}"
        result.append(f"{addr:08X}(int {addr}) - {hex_word} - {bin_word} - {mnemonic}")
    return "\n".join(result)


def expand_macros(lines: list[str]) -> list[str]:
    """
    Parses and expands macros defined in the source code using regex substitution.
    Cleans up comma artifacts in argument names and values.
    """
    macros = {}
    expanded = []
    in_macro = False
    macro_name = ""
    macro_args = []
    macro_body: list[str] = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith(".macro"):
            parts = stripped.split()
            macro_name = parts[1]
            macro_args = [a.strip(",") for a in parts[2:]]
            in_macro = True
            macro_body = []
        elif stripped == ".endmacro":
            macros[macro_name] = (macro_args, macro_body)
            in_macro = False
        elif in_macro:
            macro_body.append(line)
        else:
            tokens = stripped.split()
            if tokens and tokens[0] in macros:
                macro_name = tokens[0]
                actual_args = [a.strip(",") for a in tokens[1:]]
                formal_args, body = macros[macro_name]

                if len(actual_args) != len(formal_args):
                    raise ValueError(
                        f"Macro `{macro_name}` expects {len(formal_args)} args, got {len(actual_args)}"
                    )

                arg_map = dict(zip(formal_args, actual_args, strict=False))

                for body_line in body:

                    def replacer(match, arg_map=arg_map, body_line=body_line):
                        key = match.group(1)
                        if key not in arg_map:
                            raise ValueError(f"Unknown macro argument `\\{key}` in: {body_line}")
                        return arg_map[key]

                    replaced = re.sub(r"\\(\w+)", replacer, body_line)
                    expanded.append(replaced)
            else:
                expanded.append(line)

    return expanded


def first_pass(
    lines: list[str],
) -> tuple[dict[str, int], list[tuple[int, str, int]], list[tuple[int, str]]]:
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
            if section:  # Only update if a section is active
                org[section] = addr_of_instr
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
                _, val_str = line.split(None, 1)
                try:
                    val = int(val_str.strip(), 0)
                except ValueError:
                    # If it's a label, add it to data_segment for later resolution
                    label_map[val_str.strip()] = addr_of_instr  # Placeholder for data labels
                    val = 0  # Placeholder value, actual resolution in second_pass
                    data_segment.append((addr_of_instr, f".word {val_str.strip()}", val))

                data_segment.append(
                    (addr_of_instr, line, val)
                )  # Store line for debug, and resolved/placeholder val
                addr_of_instr += 4
            elif line.startswith(".byte"):
                _, val_str = line.split(None, 1)
                val_str = val_str.strip().strip("'\"")
                decoded = codecs.decode(val_str.encode("utf-8"), "unicode_escape")
                for c in decoded:
                    data_segment.append(
                        (addr_of_instr, f".byte {ord(c)}", ord(c))
                    )  # Store byte as int
                    addr_of_instr += 1

        elif section == ".text":
            text_segment.append((addr_of_instr, line))
            addr_of_instr += 4

    return label_map, data_segment, text_segment


def second_pass(
    segment_instructions: Sequence[tuple[int, str] | tuple[int, str, int]],
    label_map: dict[str, int],
) -> tuple[list[int], list[tuple[int, str, int]]]:
    """
    Convert instructions and data to machine code.

    Args:
        segment_instructions: List of (address, source_line) for text or
                              (address, source_line, pre_parsed_value) for data.
        label_map: A dictionary mapping label names to their resolved addresses.

    Returns:
        - list of binary instructions/data (list of ints)
        - debug info (address, source_line, encoded_value)
    """
    code = []
    debug_info = []

    for item in segment_instructions:
        addr_of_instr = item[0]
        line = item[1]

        if len(item) == 3:  # This is a data segment entry with pre-parsed value
            # For .word and .byte from data segment, item will be (addr, line_str, parsed_val)
            original_value = item[2]
            if line.startswith(".word"):
                # Re-evaluate if it was a label initially
                resolved_val = get_token(line.split()[1].strip(), label_map)
                code.append(resolved_val & 0xFFFFFFFF)
                debug_info.append((addr_of_instr, line, resolved_val))
            elif line.startswith(".byte"):
                # Already correctly parsed as an integer in first_pass for characters
                code.append(original_value & 0xFF)
                debug_info.append((addr_of_instr, line, original_value & 0xFF))
            else:
                raise ValueError(f"Unexpected data segment format: {line}")
        else:  # This is a text segment instruction
            instr, operands = parse_line(line)
            binary = encode((instr, operands), label_map, addr_of_instr)
            code.append(binary)
            debug_info.append((addr_of_instr, line, binary))
    return code, debug_info


def parse_line(line: str) -> tuple[str, list[str]]:
    parts = line.strip().split()
    instr = parts[0]
    operands = parts[1:] if len(parts) > 1 else []
    return (instr, operands)


# TODO: check if .get() with default value is ok or not
def get_token(operand: str, label_map: dict[str, int], pc: int = 0, relative: bool = False) -> int:
    """
    Converts an operand into a numeric value.

    Supported operand types:
    - 'low(label)'  — returns the lower 12 bits of the label's address.
    - 'high(label)' — returns the upper 20 bits (address rounded down to nearest 4KB), shifted.
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
    Converts a signed integer to its two's complement representation
    for a given number of bits.

    Args:
        value: The integer to convert.
        bits: The number of bits for the two's complement representation.

    Returns:
        The two's complement representation of the value.
    """
    if value < 0:
        value = (1 << bits) + value
    return value


# TODO: write comms in `return` section of types
def encode(parsed: tuple[str, list[str]], label_map: dict[str, int], addr_of_instr: int) -> int:
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
            offset_str, rs1_str = operands[1].split("(")
            rs1 = reg_to_num(rs1_str.rstrip(")"))
            imm = get_token(offset_str, label_map)
        else:
            rs1 = reg_to_num(operands[1])
            imm = get_token(operands[2], label_map)
        return ((imm & 0xFFF) << 20) | (rs1 << 15) | (info["funct3"] << 12) | (rd << 7) | opcode

    elif typ == "S":
        rs2 = reg_to_num(operands[0])
        offset_str, rs1_str = operands[1].split("(")
        rs1 = reg_to_num(rs1_str.rstrip(")"))
        imm = get_token(offset_str, label_map)
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
        # Offset is (target_label_address - current_pc)
        offset = get_token(operands[2], label_map, addr_of_instr, relative=True)

        assert offset % 2 == 0, "B-type offset must be 2-byte aligned"
        imm = twos_complement(
            offset, 13
        )  # 13 bit for sign + 12 for val, total offset includes implied 0

        imm_11 = (imm >> 11) & 0x1  # imm[11] -> instr[7]
        imm_4_1 = (imm >> 1) & 0xF  # imm[4:1] -> instr[11:8]
        imm_10_5 = (imm >> 5) & 0x3F  # imm[10:5] -> instr[30:25]
        imm_12 = (imm >> 12) & 0x1  # imm[12] -> instr[31]

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
        imm_val = get_token(operands[1], label_map)
        # imm_val from get_token for high() is already shifted by 12.
        # Now place it into the correct bit positions in the instruction (bits 31-12)
        return ((imm_val & 0xFFFFF) << 12) | (rd << 7) | opcode

    elif typ == "J":
        rd = reg_to_num(operands[0])
        # Offset is (target_label_address - current_pc)
        offset = get_token(operands[1], label_map, addr_of_instr, relative=True)
        assert offset % 2 == 0, "J-type offset must be 2-byte aligned"
        imm = twos_complement(offset, 21)  # 21 bits (including implied 0)

        imm_20 = (imm >> 20) & 0x1  # imm[20] -> instr[31]
        imm_10_1 = (imm >> 1) & 0x3FF  # imm[10:1] -> instr[30:21]
        imm_11 = (imm >> 11) & 0x1  # imm[11] -> instr[20]
        imm_19_12 = (imm >> 12) & 0xFF  # imm[19:12] -> instr[19:12]

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


def dump_bin_as_text(bin_path: str) -> None:
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


def write_binaries(
    text_code: list[int],
    data_code_debug: list[tuple[int, str, int]],
    text_debug: list[tuple[int, str, int]],
    data_debug: list[tuple[int, str, int]],
    target_path: str,
) -> None:
    """
    Writes the binary code and debug logs to files.

    Args:
        text_code: List of encoded text segment instructions (ints).
        data_code_debug: Debug info for data segment, used to generate .data.bin.
                         Contains (address, source_line_type, value).
        text_debug: Debug info for text segment (address, source_line, encoded_value).
        data_debug: Debug info for data segment (address, source_line, encoded_value).
        target_path: Base path for output files.
    """
    with open(target_path + ".data.bin", "wb") as f:
        f.write(to_bytes_data(data_code_debug))  # Use data_debug to reconstruct data bytes

    with open(target_path + ".text.log", "w", encoding="utf-8") as f:
        f.write(to_hex(text_debug))

    with open(target_path + ".data.log", "w", encoding="utf-8") as f:
        f.write(to_hex(data_debug))


def main(source_path, target_path):
    """Create .bin files and debugging info"""

    with open(source_path, encoding="utf-8") as f:
        source = f.read()

    lines = expand_macros(source.splitlines())
    label_map, data_segment, text_segment = first_pass(lines)

    if not text_segment:
        raise ValueError("No .text segment found or no instructions in .text segment.")
    text_segment_start_address = text_segment[0][0]

    # TODO: refactor

    # data_code will be a flat list of bytes/words, data_debug will have source info
    data_code_list, data_debug = second_pass(data_segment, label_map)
    text_code, text_debug = second_pass(text_segment, label_map)

    # a little messy, but i had to do it since i gotta put initial text segment addr
    with open(target_path + ".text.bin", "wb") as f:
        f.write(to_bytes_text(text_code, text_segment_start_address))

    # Pass data_debug to write_binaries for .data.bin generation
    write_binaries(text_code, data_debug, text_debug, data_debug, target_path)
    print(".text and .data binaries generated.")


if __name__ == "__main__":
    assert len(sys.argv) == 3, "Wrong arguments: translator.py <input_file> <target_file>"
    _, source, target = sys.argv
    main(source, target)
