# run_machine.py
import sys

from machine.machine import CPU


def load_binary(path):
    with open(path, "rb") as f:
        return f.read()


def dump_snapshot(cpu, path="out/final_snapshot.txt"):
    with open(path, "w") as f:
        f.write("[Registers]\n")
        for i in range(0, 32, 4):
            line = " ".join(f"r{j:02d}={cpu.registers[j]:08X}" for j in range(i, i + 4))
            f.write(line + "\n")

        # Dump memory: 0x300..0x340 (example range)
        f.write("\n[Memory @ 0x300]\n")
        for addr in range(0x300, 0x340, 4):
            # Ensure we don't try to read beyond allocated memory
            if addr + 4 <= len(cpu.data_mem):
                word = int.from_bytes(cpu.data_mem[addr : addr + 4], "little")
                f.write(f"{addr:08X}: {word:08X}\n")
            else:
                f.write(f"{addr:08X}: (out of bounds)\n")

        # Dump output buffer
        f.write("\n[Output buffer]\n")
        if all(isinstance(x, int) for x in cpu.output_buffer):
            # Join integers with newline, making sure each is converted to string
            output = "\n".join(str(x) for x in cpu.output_buffer)
        else:
            # Join characters directly
            output = "".join(cpu.output_buffer)

        f.write(output + "\n")


def run(instr_path, data_path, input_file=None, input_mode="bytes"):
    full_instr_mem = load_binary(instr_path)
    data_mem_bytes = load_binary(data_path)

    # The first 4 bytes of the .text.bin file contain the entry point address
    entry_pc = int.from_bytes(full_instr_mem[:4], "little")
    instr_bytes = full_instr_mem[4:]
    entry_pc = int.from_bytes(
        full_instr_mem[:4], "little"
    )  # the first 4 bytes to get the start addr of instructions

    # Allocate instruction memory (e.g., 64 KB)
    instr_mem = bytearray(64 * 1024)
    # Place instructions at specific place in mem (from the start addr)
    if entry_pc + len(instr_bytes) > len(instr_mem):
        raise ValueError("Instruction memory overflow: instructions exceed allocated 64KB.")
    instr_mem[entry_pc : entry_pc + len(instr_bytes)] = instr_bytes

    cpu = CPU(instr_mem, data_mem_bytes)
    cpu.pc = entry_pc

    if input_file:
        cpu.load_input_file(input_file, as_words=(input_mode == "words"))

    print("==== MACHINE START ====")
    # TODO: make step_count the same as tick_count in Microcode
    step_count = 0
    max_steps = 100_000
    while cpu.running:
        cpu.step()
        step_count += 1
        # sort for 30 nums requires more than 10_000 steps MonkaS
        if step_count > max_steps:
            print("Execution stopped: too many steps")
            break

    print("==== MACHINE HALTED ====")
    cpu.logger.finish()

    print("Output buffer:")
    # pretty print
    if all(isinstance(x, int) for x in cpu.output_buffer):
        print("\n".join(str(x) for x in cpu.output_buffer))
    else:
        print("".join(str(x) for x in cpu.output_buffer))

    dump_snapshot(cpu)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(
            "Usage: python run_machine.py <text_bin> <data_bin> [input_file] [--input-mode=bytes|words]"
        )
        sys.exit(1)

    instr_bin = sys.argv[1]
    data_bin = sys.argv[2]
    input_file = None
    input_mode = None

    # Parse arguments starting from the third one
    for arg in sys.argv[3:]:
        if arg.startswith("--input-mode="):
            input_mode = arg.split("=")[1]
            if input_mode not in {"bytes", "words"}:
                print("Error: --input-mode must be 'bytes' or 'words'")
                sys.exit(1)
        else:
            if input_file is not None:
                print("Error: multiple input files specified. Only one input file is supported.")
                sys.exit(1)
            input_file = arg

    # Warning if mode not specified when input_file is provided
    if input_file and input_mode is None:
        print("[WARNING] No --input-mode specified. Assuming 'bytes'")
        input_mode = "bytes"

    # If no input file is provided, input_mode should remain None or default to something sensible
    if input_file is None:
        input_mode = (
            None  # Reset if no input file, so load_input_file isn't called with default mode
        )

    run(instr_bin, data_bin, input_file, input_mode)
