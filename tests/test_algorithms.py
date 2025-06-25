import os
import shutil
import subprocess

import pytest

ALGO_DIR = "algorithms"
EXPECTED_DIR = "tests/expected"
OUT_DIR = "out"
TRACE_PATH = "log_output/trace.log"
TARGET_PREFIX = "out/out"
SNAPSHOT_PATH = os.path.join(OUT_DIR, "final_snapshot.txt")

TEST_CASES = [
    {
        "name": "hello_world",
        "input_file": None,
        "input_mode": None,
    },
    {
        "name": "sort",
        "input_file": "algorithms/sort_input.txt",
        "input_mode": "words",
    },
    {
        "name": "hello_user_name",
        "input_file": "algorithms/hello_user_name_input.txt",
        "input_mode": None,
    },
    {
        "name": "cat",
        "input_file": "algorithms/cat_input.txt",
        "input_mode": None,
    },
    {"name": "macro_showcase", "input_file": None, "input_mode": None},
]


def _read(path):
    with open(path) as f:
        return f.read().strip()


@pytest.mark.parametrize("case", TEST_CASES)
def test_algorithm(case):
    name = case["name"]
    asm_path = os.path.join(ALGO_DIR, f"{name}.asm")
    expected_path = os.path.join(EXPECTED_DIR, name)
    output_dir = os.path.join("test_outputs", name)

    input_file = case.get("input_file")
    input_mode = case.get("input_mode")

    # === Clearing out/ and log_output/ ===
    if os.path.exists(OUT_DIR):
        shutil.rmtree(OUT_DIR)
    os.makedirs(OUT_DIR, exist_ok=True)

    if os.path.exists("log_output"):
        shutil.rmtree("log_output")
    os.makedirs("log_output", exist_ok=True)

    # === Cleanup and preparation of test_outputs/<name>/ ===
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir)

    # === 1. Translation .asm -> .bin ===
    target_prefix = os.path.join(OUT_DIR, "out")  # out/out.text.bin
    subprocess.run(["python", "machine/translator.py", asm_path, target_prefix], check=True)

    # === 2. Starting the machine ===
    cmd = ["python", "run_machine.py", f"{target_prefix}.text.bin", f"{target_prefix}.data.bin"]
    if input_file:
        cmd.append(input_file)
    if input_mode:
        cmd.append(f"--input-mode={input_mode}")

    subprocess.run(cmd, check=True)

    # === 3. Copy all artifacts to test_outputs/<name>/ ===
    artifacts = [
        ("log_output/trace.log", "trace.log"),
        (os.path.join(OUT_DIR, "final_snapshot.txt"), "final_snapshot.txt"),
        (os.path.join(OUT_DIR, "out.text.log"), "out.text.log"),
        (os.path.join(OUT_DIR, "out.data.log"), "out.data.log"),
    ]

    for src, dst_name in artifacts:
        if os.path.exists(src):
            shutil.copy(src, os.path.join(output_dir, dst_name))

    # === 4. Comparison with reference files ===
    for _src, dst_name in artifacts:
        actual = os.path.join(output_dir, dst_name)
        expected = os.path.join(expected_path, dst_name)
        assert os.path.exists(actual), f"Missing output file: {actual}"
        assert os.path.exists(expected), f"Missing expected file: {expected}"
        assert _read(actual) == _read(expected), f"Mismatch in file: {dst_name}"
