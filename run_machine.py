import sys

from machine.machine import CPU


def load_binary(path):
    with open(path, "rb") as f:
        return f.read()


def run(instr_path, data_path):
    instr_mem = load_binary(instr_path)
    data_mem = load_binary(data_path)
    cpu = CPU(instr_mem, data_mem)

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


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python machine.py <text_bin> <data_bin>")
    else:
        run(sys.argv[1], sys.argv[2])
