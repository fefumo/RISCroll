# RISCroll
```
                                       ____________________________
                                      /                           /\
                                     /                           / /\ 
                                    /     =================     / /
                                   /     /    RISC-V      /   / \/
                                  /     /    32-bit      /    /\
                                 /     /================/    / /
                                /___________________________/ /
                                \___________________________\/
                                 \ \ \ \ \ \ \ \ \ \ \ \ \ \ \
```
RUSSIAN README: [README_RU.md](README_RU.md)

Laboratory Work No. 4. Experiment

Molchanov Fyodor Denisovich, P3213

## Programming Language
### Syntax

```ebnf
<program>         ::= {<line> | <macro_def>}

<line>            ::= <label_line> | <code_line> | <comment_line>

<label_line>      ::= <label> [<comment>] <newline>

<code_line>       ::= [<label>] (<instruction> | <directive> | <macro_use>) [<comment>] <newline>

<comment_line>    ::= <comment> <newline>

<label>           ::= <identifier> ":"

<directive>       ::= "." <identifier> [<value_list>]

<value_list>      ::= <value> { "," <value> }

<value>           ::= <identifier> 
                        | <number> 
                        | <string>
                        | "high(" <identifier> ")"
                        | "low(" <identifier> ")"

<string>          ::= '"' { <any_char_except_quote> } '"'

<instruction>     ::= <r_type_instr>
                        | <i_arith_instr>
                        | <i_load_instr>
                        | <i_jump_instr>
                        | <s_type_instr>
                        | <b_type_instr>
                        | <u_type_instr>
                        | <j_type_instr>
                        | <sys_instr>

<r_type_instr>    ::= ("add" | "sub" | "mul" | "div" | "lsl" | "lsr" | "and" | "or" | "xor")
                     <reg> "," <reg> "," <reg>

<i_arith_instr> ::= ("addi" | "andi" | "ori")
                    <reg> "," <reg> "," <immediate>

<i_load_instr>  ::= "lw"
                    <reg> "," <offset> "(" <reg> ")"

<i_jump_instr>  ::= "jalr"
                    <reg> "," <offset> "(" <reg> ")"


<s_type_instr>    ::= ("sw") <reg> "," <offset> "(" <reg> ")"

<b_type_instr>    ::= ("beq" | "bne" | "bgt" | "ble" | )  <reg> "," <reg> "," <label_ref>

<u_type_instr>    ::= ("lui" | "auipc") <reg> "," <immediate>

<sys_instr>       ::= "halt"

<j_type_instr>    ::= "jal" <reg> "," <label_ref>

<comment>         ::= "#" { <any_char_except_newline> }

<reg>             ::= "$r" <number>         // $r0 to $r31

<offset>          ::= <number>
<immediate>       ::= <number>
<label_ref>       ::= <identifier>

<identifier>      ::= <letter> { <letter> | <digit> | "_" }

<number> ::= ["-"] (<decimal> | <hexadecimal>)

<decimal>     ::= <digit> {<digit>}
<hexadecimal> ::= "0x" <hex_digit> {<hex_digit>}

<hex_digit>   ::= <digit> | "a" | "b" | "c" | "d" | "e" | "f"
                             | "A" | "B" | "C" | "D" | "E" | "F"

<letter>          ::= "A" | ... | "Z" | "a" | ... | "z"
<digit>           ::= "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9"

<macro_def> ::= ".macro" <identifier> [<macro_param_list>] <newline>
                { <line> }
                ".endm" <newline>

<macro_param_list> ::= <identifier> { "," <identifier> }

<macro_use> ::= <identifier> [<macro_arg_list>]

<macro_arg_list> ::= <value> { "," <value> }

```
##### Support for labels, sections, and the .org directive. Demonstration of macros.
The described syntax allows writing code as in full-fledged assembly.

Example of using labels, sections, and the .org directive:
```
.data
.org 0x0200
in_addr: .word 0x100

.text
.org 0x1000
main:
    halt
```

Example of using a macro:
```
.macro load_addr reg, label
    lui \reg, high(\label)
    addi \reg, \reg, low(\label)
    lw \reg, 0(\reg)
.endmacro
```

Used in: [macro_showcase.asm](algorithms/macro_showcase.asm)

### Registers
| Register | Alias  | Description                       |
|----------|--------|-----------------------------------|
| `r0`    | `zero` | Constant zero                     |
| `r1`    | `ra`   | Return address                    |
| `r2`    | `sp`   | Stack pointer                     |
| `r3`    | `gp`   | Global pointer (optional)         |
| `r4`    | `tp`   | Thread pointer (optional)         |
| `r5`    | `t0`   | Temporary                         |
| `r6`    | `t1`   | Temporary                         |
| `r7`    | `t2`   | Temporary                         |
| `r8`    | `s0`   | Saved register / frame pointer    |
| `r9`    | `s1`   | Saved register                    |
| `r10`   | `s2`   | Saved register                    |
| `r11`   | `s3`   | Saved register                    |
| `r12`   | `s4`   | Saved register                    |
| `r13`   | `s5`   | Saved register                    |
| `r14`   | `s6`   | Saved register                    |
| `r15`   | `s7`   | Saved register                    |
| `r16`   | `a0`   | Function argument / syscall return |
| `r17`   | `a1`   | Function argument                 |
| `r18`   | `a2`   | Function argument                 |
| `r19`   | `a3`   | Function argument                 |
| `r20`   | `a4`   | Function argument                 |
| `r21`   | `a5`   | Function argument                 |
| `r22`   | `a6`   | Function argument                 |
| `r23`   | `a7`   | Syscall code                      |
| `r24`   | `t3`   | Temporary                         |
| `r25`   | `t4`   | Temporary                         |
| `r26`   | `t5`   | Temporary                         |
| `r27`   | `t6`   | Temporary                         |
| `r28`   | `x28`  | Reserved / custom use             |
| `r29`   | `x29`  | Reserved / custom use             |
| `r30`   | `x30`  | Reserved / custom use             |
| `r31`   | `x31`  | Reserved / custom use             |

### Computation Strategy
- The assembler follows a strict computation model. All arguments are evaluated before applying functions to them.
- The language does not support expressions involving multiple arithmetic/logical operations. The order of operations is determined by the programmer.
- All instruction arguments are either registers or simple immutable values (literals) evaluated during translation.
- All pseudo-functions (high(label), low(label)) are expanded during translation. Only primitive instructions remain during execution.

### Scoping
The language does not have explicit scoping, but there are a few points:
- The data and code sections do not have direct access to each other.
- At the hardware level, it is impossible to read an instruction from instruction memory as data and vice versa.
- Labels (label:) have global scope, regardless of the section they are declared in.
- A name cannot be reused for different objects (the same string cannot be both a label, a macro, and a variable).
- Symbol resolution is performed before execution, during translation (not dynamically).

### Typing, Types of Literals
- .word — 32-bit values
- .byte — 8-bit
- 0x literals
- Pseudo-functions high(), low()

## Memory Organization
- The processor uses byte-addressable memory.
- Load/store instructions (lw, sw) work with 4-byte words.
- Immediate offsets in memory instructions are 12-bit signed values, allowing access to +-2048 bytes around the base register.
- The memory model follows Harvard architecture.
- There are three types of memory: Instruction Memory, Data Memory, Microinstruction Memory.

### Microcode Structure

Each microinstruction (`MicroInstruction`) defines one clock cycle of instruction execution. Below are the fields and their descriptions:

|    Field     |       Type       |       Possible Values       |                         Purpose                          |
| :---------: | :-------------: | :----------------------------: | :---------------------------------------------------------: |
| `latch_pc`  | `Optional[str]` |  `"inc"`, `"alu"`, `"branch"`  | PC control: increment, load from ALU, conditional branch |
| `latch_ir`  |     `bool`      |        `True` / `False`        |        Load instruction from memory at `PC` into `IR`        |
| `latch_reg` | `Optional[int]` |            `0..31`             |        Register number to write to        |
| `latch_alu` | `Optional[str]` | `"add"`, `"sub"`, ..., `"lui"` |         ALU operation to perform         |
| `latch_ar`  | `Optional[str]` |               —                |              Reserved (unused)              |
| `mem_read`  |     `bool`      |        `True` / `False`        |      Read data from `data_mem` at address `ALU_OUT`       |
| `mem_write` |     `bool`      |        `True` / `False`        |      Write data to `data_mem` at address `ALU_OUT`       |
| `set_flags` |     `bool`      |        `True` / `False`        |     Set flags `Z`, `N` based on ALU result     |
| `next_mpc`  | `Optional[int]` |       microinstruction address       |        Next microinstruction address in microprogram        |
|  `jump_if`  | `Optional[str]` | `"Z"`, `"NZ"`, `"GT"`, `"LE"`  |         Branch condition (for `latch_pc="branch"`)          |
|   `halt`    |     `bool`      |        `True` / `False`        |                Stop machine execution                |
              |

#### Initial Microinstructions

| MPC  | Comment       |                         Description                          |
| ---- | ----------------- | :-------------------------------------------------------: |
| 0    | `FETCH`           |     Load instruction from `instr_mem` into `IR`, `PC += 4`     |
| 1    | `DECODE`          |            Jump to common decoding point            |
| 1000 | `DECODE DISPATCH` | Find the required microprogram by `(opcode, funct3, funct7)` |


### Instruction Fetch
- The program counter (PC) points to text memory.
- Instructions are 4 bytes (32 bits) long and must be word-aligned.
- The processor increments PC by += 4 after each instruction unless a branch occurs.

### Data Access
- Memory access is only allowed through registers: all load and store instructions (lw, sw) require an address in a register.
- The lw (load word) instruction loads 4 bytes from memory at the address contained in the register.
- The sw (store word) instruction writes 4 bytes to a similar address.
- Immediate values cannot be passed to lw/sw — only through lui/addi or address registers.
- I\O addresses are currently strict: input -- 0x1, output -- 0x2. In the future, the programmer will be able to choose these addresses.

```
       Instruction memory
        +-----------------------------+
        |      Instruction Memory     |  <-- Read-only (READ-ONLY)
        | 0x0000: bin instr           |
        | 0x0004: bin instr           |
        |  ...                        |
        +-----------------------------+

        +-----------------------------+
        |         Data Memory         |  <-- Read / Write
        | 0x1000: user data           |
        | 0x1004: user data           |
        |  ...                        |
        +-----------------------------+

        +-----------------------------+
        |      Memory-mapped I/O      |
        | 0x1: IN_BUF                 |  <-- Read-only
        | 0x2: OUT_BUF                |  <-- Write-only
        +-----------------------------+

        +-----------------------------+
        |     Microprogram Memory     |  <-- CU-only, control signals
        | 0x0000: signals             |
        | 0x0001: signals             |
        |  ...                        |
        +-----------------------------+

```

## Instruction Set
#### Main features:
 - Strict instruction length, 32 bits
 - `opcode` values and instruction formats are taken from the official RISC-V documentation
 - `jal` is implemented exactly as in RISC-V, including accounting for r0 as an unused register for writing. In this case, `jal` will be used as `goto <label>` without writing to the return register. The range of values, since `imm value` is 20 bits, will be `[-2^31; 2^31 - 2^12] = [−2147483648, 2147479552]`
 - Each command takes at least 2 clock cycles for fetch and decode, then, depending on the type of microprogram, from 1 to ~3 microinstructions are executed.

#### Abbreviations:
- rs - source register
- rd - destination register
- opcode - operation code
- funct - function fields
- imm - immediate value 


|  Type  |       Example Instructions       | Opcode (bin) | Opcode (hex) |            Notes            |
| :----: | :------------------------------: | :----------: | :----------: | :-------------------------: |
| R-type | add, sub, mul, div, and, or, xor |  `0110011`   |    `0x33`    |   ALU register operations   |
| I-type |         addi, andi, ori          |  `0010011`   |    `0x13`    |      ALU immediate ops      |
| I-type |              lw, lb              |  `0000011`   |    `0x03`    |      Load instructions      |
| I-type |               jalr               |  `1100111`   |    `0x67`    |        Indirect jump        |
| S-type |                sw                |  `0100011`   |    `0x23`    |     Store instructions      |
| B-type |        beq, bne, blt, bge        |  `1100011`   |    `0x63`    |    Conditional branches     |
| U-type |               lui                |  `0110111`   |    `0x37`    |    Load upper immediate     |
| U-type |              auipc               |  `0010111`   |    `0x17`    | PC-relative upper immediate |
| J-type |               jal                |  `1101111`   |    `0x6F`    |  Unconditional jump + link  |
|  SYS   |               halt               |  `1111111`   |    `0x7F`    |     Custom system/halt      |

* `opcode` — always in `[6..0]`
* `funct3` — always in `[14..12]`
* `funct7` (if present) — always in `[31..25]`

---
#### R-type Instructions

Format:

|  funct7  |   rs2    |   rs1    |  funct3  |   rd    | opcode |
| :------: | :------: | :------: | :------: | :-----: | :----: |
| [31..25] | [24..20] | [19..15] | [14..12] | [11..7] | [6..0] |


Instructions:

| Instruction | funct7  | funct3 | opcode (0x33) |    Description    |
| :---------: | :-----: | :----: | :-----------: | :---------------: |
|     add     | 0000000 |  000   |    0110011    | `rd = rs1 + rs2`  |
|     sub     | 0000000 |  001   |    0110011    | `rd = rs1 - rs2`  |
|     and     | 0000000 |  010   |    0110011    | `rd = rs1 & rs2`  |
|     or      | 0000000 |  011   |    0110011    | `rd = rs1 \| rs2` |
|     xor     | 0000000 |  100   |    0110011    | `rd = rs1 ^ rs2`  |
|     mul     | 0000000 |  101   |    0110011    | `rd = rs1 * rs2`  |
|     div     | 0000000 |  110   |    0110011    | `rd = rs1 / rs2`  |
|     lsl     | 0000000 |  111   |    0110011    | `rd = rs1 << rs2` |
|     lsr     | 0000001 |  000   |    0110011    | `rd = rs1 >> rs2` |

---

#### I-type Instructions

Format:

| imm[11:0] |   rs1    |  funct3  |   rd    | opcode |
| :-------: | :------: | :------: | :-----: | :----: |
| [31..20]  | [19..15] | [14..12] | [11..7] | [6..0] |

Instructions:

| Instruction | funct3 | opcode  |                   Description                    |
| :---------: | :----: | :-----: | :----------------------------------------------: |
|    addi     |  000   | 0010011 |                 `rd = rs1 + imm`                 |
|    andi     |  001   | 0010011 |                 `rd = rs1 & imm`                 |
|     ori     |  010   | 0010011 |                `rd = rs1 \| imm`                 |
|     lw      |  000   | 0000011 |   `rd = 32-bit word at mem[rs1 + offset]<br>`    |
|     lb      |  001   | 0000011 | ``rd ← sign-extended byte at mem[rs1 + offset]`` |
|    jalr     |  000   | 1100111 |            `PC = (rs1 + offset) & ~1`            |


---
#### S-type Instructions

Format:

| imm[11:5] |   rs2    |   rs1    |  funct3  | imm[4:0] | opcode |
| :-------: | :------: | :------: | :------: | :------: | :----: |
| [31..25]  | [24..20] | [19..15] | [14..12] | [11..7]  | [6..0] |

Instructions:


| Instruction | funct3 | opcode  |         Description          |
| :---------: | :----: | :-----: | :--------------------------: |
|     sw      |  000   | 0100011 |    `mem[rs1 + imm] = rs2`    |
|     sb      |  001   | 0100011 | `byte at mem[rs1+imm] = rs2` |

---
#### B-type Instructions

Format:

| imm[12] | imm[10:5] |   rs2    |   rs1    |  funct3  | imm[4:1] | imm[11] | opcode |
| :-----: | :-------: | :------: | :------: | :------: | :------: | :-----: | :----: |
|  [31]   | [30..25]  | [24..20] | [19..15] | [14..12] | [11..8]  |   [7]   | [6..0] |


> After assembly, all immediate parts are concatenated back into a 12-bit offset.

Instructions:

| Instruction | funct3 | opcode  |          Description          |
| :---------: | :----: | :-----: | :---------------------------: |
|     beq     |  000   | 1100011 | `if rs1 == rs2, PC += offset` |
|     bne     |  001   | 1100011 | `if rs1 != rs2, PC += offset` |
|     bgt     |  010   | 1100011 | `if rs1 > rs2, PC += offset`  |
|     ble     |  011   | 1100011 | `if rs1 <= rs2, PC += offset` |

---
#### U-type Instructions

Format:

| imm[31:12] |   rd    | opcode |
| :--------: | :-----: | :----: |
|  [31..12]  | [11..7] | [6..0] |

Instructions:

| Instruction | opcode  |   Description    |
| :---------: | :-----: | :--------------: |
|     lui     | 0110111 | `rd = imm << 12` |

---

#### J-type Instructions

Format:

| imm[20] | imm[10:1] | imm[11] | imm[19:12] |   rd    | opcode |
| :-----: | :-------: | :-----: | :--------: | :-----: | :----: |
|  [31]   | [30..21]  |  [20]   |  [19..12]  | [11..7] | [6..0] |
> After concatenation: `offset = {imm[20], imm[10:1], imm[11], imm[19:12]} << 1`

Instructions:

| Instruction | opcode  |          Description          |
| :---------: | :-----: | :---------------------------: |
|     jal     | 1101111 | `rd = PC+4; PC = PC + offset` |

---
#### sys-type

Format

| instruction | operands | opcode (bin) | opcode (hex) |    description     |
| :---------: | :------: | :----------: | :----------: | :----------------: |
|   `halt`    |    –     |  `1111111`   |    `0x7F`    | Custom system/halt |

## Translator

Translation occurs in several stages:

1. **First Pass (`first_pass`)**  
   - Skip comments (`#`).
   - Code is divided into `.text` and `.data` sections, each with its own addressing space (due to Harvard architecture).
   - Process `.org` directives.
   - Extract and save labels (labels) along with their addresses.
   - Form two segments: `data_segment` and `text_segment`, containing pairs `(address, string)`.

2. **Second Pass (`second_pass`)**  
   Here, actual translation occurs:
   - Each segment line is analyzed and converted into a numerical representation.
   - Labels with `.word` and `.byte` are translated into memory and will be located at `out/<out_path>.data.bin`.
   - For `.text` instructions, a parser (`parse_line`) and encoder (`encode`) are used to form 32-bit binary code according to the ISA description.
   - Debug information is generated in parallel: `(address, source line, machine code)`.

3. **Output Binary Files (`write_binaries`)**  
   - The resulting codes are saved into two separate binary files:  
     - `.text.bin` — program code (instructions)  
     - `.data.bin` — initial data memory state  
   - Debug text dumps `.text.log` and `.data.log` are also created, where each line contains:  
     `address — HEX — BIN — source line`.

## Processor Model
__RISC, lol?__
> The input is a translated (via [translator.py](machine/translator.py)) binary file, output name, and (optionally) an input data file.

From [run_machine.py](run_machine.py):
```text
Usage: python run_machine.py <text_bin> <data_bin> [input_file]
```

Running the translator:
```text
Usage: python machine/translator.py <asm file> <desired output file name>
```

The emulator can generate detailed logs (in `trace.log`) with line-by-line information:
- clock cycle number;
- register states;
- IR, PC, ALU_OUT, flags;
- CU action comments.
This allows precise tracking of program behavior at the microinstruction level.

### Circuit Design
Model features:
- Fixed-length instructions (32 bits);
- 7 instruction types (R, I, S, B, U, J, SYS);
- Harvard architecture memory (separate instruction and data);
- Input/output processing via memory-mapped I/O;
- Limited flag system (N, Z).

#### Datapath

Datapath consists of:
- Instruction register (IR);
- Program counter (PC);
- ALU (Arithmetic Logic Unit);
- General-purpose registers (32 x 32-bit);
- Multiplexers for ALU input and memory addressing selection;
- Data and address buses.

![Datapath](lab4_Datapath.png)

---

#### Control Unit

Control Unit is implemented via microprogram memory, where each microinstruction defines:
   - Control signals (read/write, register selection, ALU operations);
   - Transition to the next microinstruction;
   - Branch conditions based on N/Z flags and instruction type.

The microprogram defines the exact sequence of steps for each clock cycle of instruction execution.

![Control Unit](lab4_CU.drawio.png)


## ✅ Testing

Testing is implemented as **golden tests** — each test `.asm` file is executed, and the resulting output files are compared with pre-saved **reference results** (logs, memory snapshots, etc.).

### 🔧 Tools Used:

* [`pytest`](https://docs.pytest.org/) — for running and managing tests;
* [`GitHub Actions`](https://docs.github.com/en/actions) — for automatic CI on each `push` and `pull request`;
* `tests/expected/<name>/` — folders with expected (golden) logs;
* `test_outputs/<name>/` — logs for each test are saved (always), even if the test fails.

---

### What is Checked in Each Test:

For each algorithm:

1. Translation `.asm` -> `.bin` is performed;
2. `run_machine.py` is run on the resulting files;
3. Execution logs are saved:
   * `trace.log` (CU microsteps);
   * `final_snapshot.txt` (register and memory snapshot);
   * `out.text.log` (instructions in hex and disassembled form);
   * `out.data.log` (`.data` section dump);
4. The logs are compared with `tests/expected/<test>/`.

---

### 🚀 Manual Test Execution

In the project root:

```bash
pytest -v
```

Tests can be limited to a specific file or test:

```bash
pytest tests/test_algorithms.py::test_algorithm[hello_world]
```

---

### 💚 CI: GitHub Actions

CI workflow `.github/workflows/test.yml` is configured:

* runs on each `push` or `pull_request`;
* builds and tests all `.asm` files;
* fails if any result does not match the expected one.