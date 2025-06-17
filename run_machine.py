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

        # Dump memory: 0x100..0x140
        f.write("\n[Memory @ 0x100]\n")
        for addr in range(0x100, 0x140, 4):
            word = int.from_bytes(cpu.data_mem[addr:addr+4], "little")
            f.write(f"{addr:08X}: {word:08X}\n")

        # Dump output buffer
        f.write("\n[Output buffer]\n")
        try:
            output = "".join(cpu.output_buffer)
        except TypeError:
            output = "".join(map(chr, cpu.output_buffer))
        f.write(output + "\n")


def run(instr_path, data_path, input_file=None):
    full_instr_mem = load_binary(instr_path)
    data_mem = load_binary(data_path)

    instr_bytes = full_instr_mem[4:]
    entry_pc = int.from_bytes(
        full_instr_mem[:4], "little"
    )  # the first 4 bytes to get the start addr of instructions

    # allocate 64 KB
    instr_mem = bytearray(64 * 1024)
    # put instructions at specific place in mem (from the start addr)
    instr_mem[entry_pc : entry_pc + len(instr_bytes)] = instr_bytes

    cpu = CPU(instr_mem, data_mem)
    cpu.pc = entry_pc

    if input_file:
        cpu.load_input_file(input_file)

    print("==== MACHINE START ====")
    # TODO: make step_count the same as tick_count in Microcode
    step_count = 0
    while cpu.running:
        cpu.step()
        step_count += 1
        if step_count > 10_000:
            print("Execution stopped: too many steps")
            break

    print("==== MACHINE HALTED ====")
    cpu.tracer.finish()

    print("Output buffer:")
    print("".join(cpu.output_buffer))
    
    dump_snapshot(cpu)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python run_machine.py <text_bin> <data_bin> [input_file]")
    else:
        instr_bin = sys.argv[1]
        data_bin = sys.argv[2]
        input_file = sys.argv[3] if len(sys.argv) > 3 else None
        run(instr_bin, data_bin, input_file)
