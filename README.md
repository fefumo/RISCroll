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
Лабораторная работа №4. Эксперимент

Молчанов Фёдор Денисович, P3213
`asm | risc | harv | mc | tick | binary | stream | mem | pstr | prob2 | vector`

## Язык программирования
### Синтаксис

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
##### Поддержка label-ов, секций и директивы .org. Поддержка пользовательских макроопределений.
Описанный синтаксис позволяет писать код как на полноценном асме.

Пример использования лейблов, секций и директивы .org:
```
.data
.org 0x0200
in_addr: .word 0x100

.text
.org 0x1000
main:
    halt
```

Пример использования макроса:
```
.macro inc3 reg
    addi \reg, \reg, 3
.endm

inc3 r5 # использование макроса inc3 в коде

```
### Регистры
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

### Стратегия вычислений
- Ассемблер соответствует строгой модели вычислений. Все аргументы вычисляются до применения к ним функций
- Язык не поддерживает выражения включающие в себя несколько ариф./логич. операций. Порядок выполнения операций определяет программист
- Все аргументы инструкций -- либо регистры, либо простые немодифицируемые значения (литералы), вычисляемые на этапе трансляции
- Все псевдо-функции (high(label), low(label)) раскрываются во время трансляции. Во время исполнения остаются только примитивные инструкции.

### Области видимости
В языке не существует как таковых областей видимости, однако есть пара моментов:
- Секция данных и команд не имеют прямого доступа друг к другу
- На аппаратном уровне невозможно прочитать команду из памяти команд как данные и наоборот
- Метки (label:) имеют глобальную область видимости, независимо от секции, в которой объявлены
- Имя не может быть повторно использовано для разных объектов (одна и та же строка не может быть и меткой, и макросом, и переменной)
- Разрешение символов производится до выполнения, на этапе трансляции (не динамически)

### Типизация, виды литералов
- .word — 32-битные значения
- .byte — 8-битные
- 0x литералы
- псевдо-функции high(), low()

## Организация памяти
- Процессор использует память с байтовой адресацией.
- Инструкции загрузки/сохранения (lw, sw) работают с 4-байтовыми словами.
- Непосредственные смещения в инструкциях памяти представляют собой 12-битные значения со знаком, что позволяет получить доступ к +-2048 байтам вокруг базового регистра.
- Модель памяти соответствует Гарвардской архитектуре
- Присутствует 3 вида памяти: Память инструкций, Память данных, Память микрокоманд

### Извлечение инструкций
- Счетчик программ (PC) указывает на текстовую память.
- Инструкции имеют длину 4 байта (32 бита) и должны быть выровнены по словам.
- Процессор увеличивает PC на += 4 после каждой инструкции, если только не происходит переход или переход.

### Доступ к данным
- Обращение к памяти происходит только через регистры
- Доступ к отображенному в память вводу-выводу осуществляется с помощью обычных инструкций lw / sw по предопределенным адресам.
- Память команд является read-only на аппаратном уровне

```
       Instruction memory
+-----------------------------+
| 00       bin instr          |
| 01       bin instr          |
|      ...                    |
+-----------------------------+


        Data Memory                  I\O
+-----------------------------+    +-------+
| 00       data               | <--|IN_BUF |
| 01       data               | <--|OUT_BUF|
|      ...                    |    +-------+
| 10       data               |
| 11       data               |
|      ...                    |
+-----------------------------+
|            Stack            |
+-----------------------------+
| ???      end                |
|      ...                    |
| MAX      begin              |
+-----------------------------+

       Microprogram memory
+-----------------------------+
| 00       signals            |
| 01       signals            |
|      ...                    |
+-----------------------------+
```

## Система команд
 - Длина инструкции строгая, 32 бит

> rs - source register

> rd - destination register

> opcode - operation code

> funct - function fields

> imm - immediate value 


|  Type  |       Example Instructions       | Opcode (bin) | Opcode (hex) |            Notes            |
| :----: | :------------------------------: | :----------: | :----------: | :-------------------------: |
| R-type | add, sub, mul, div, and, or, xor |  `0110011`   |    `0x33`    |   ALU register operations   |
| I-type |         addi, andi, ori          |  `0010011`   |    `0x13`    |      ALU immediate ops      |
| I-type |                lw                |  `0000011`   |    `0x03`    |      Load instructions      |
| I-type |               jalr               |  `1100111`   |    `0x67`    |        Indirect jump        |
| S-type |                sw                |  `0100011`   |    `0x23`    |     Store instructions      |
| B-type |        beq, bne, blt, bge        |  `1100011`   |    `0x63`    |    Conditional branches     |
| U-type |               lui                |  `0110111`   |    `0x37`    |    Load upper immediate     |
| U-type |              auipc               |  `0010111`   |    `0x17`    | PC-relative upper immediate |
| J-type |               jal                |  `1101111`   |    `0x6F`    |  Unconditional jump + link  |
|  SYS   |               halt               |  `1111111`   |    `0x7F`    |     Custom system/halt      |

#### R-type инструкции
Формат:

|  funct7  |   rs2    |   rs1    |  funct3  |   rd    | opcode |
| :------: | :------: | :------: | :------: | :-----: | :----: |
| `[31..25]` | `[24..20]` | `[19..15]` | `[14..12]` | `[11..7]` | `[6..0]` |
|  7 bits  |  5 bits  |  5 bits  |  3 bits  | 5 bits  | 7 bits |

Инструкции и их бинарное представление:

| Instruction |  funct7   | rs2 | rs1 | funct3 | rd  | opcode (`0x33`) |    description    |
| :---------: | :-------: | :-: | :-: | :----: | :-: | :-------------: | :---------------: |
|     add     | `0000000` |  -  |  -  | `000`  |  -  |    `0110011`    | `rd = rs1 + rs2`  |
|     sub     | `0000000` |  -  |  -  | `001`  |  -  |    `0110011`    | `rd = rs1 - rs2`  |
|     and     | `0000000` |  -  |  -  | `010`  |  -  |    `0110011`    | `rd = rs1 & rs2`  |
|     or      | `0000000` |  -  |  -  | `011`  |  -  |    `0110011`    | `rd = rs1 \| rs2` |
|     xor     | `0000000` |  -  |  -  | `100`  |  -  |    `0110011`    | `rd = rs1 ^ rs2`  |
|     mul     | `0000000` |  -  |  -  | `101`  |  -  |    `0110011`    | `rd = rs1 * rs2`  |
|     div     | `0000000` |  -  |  -  | `110`  |  -  |    `0110011`    | `rd = rs1 / rs2`  |
|     lsl     | `0000000` |  -  |  -  | `111`  |  -  |    `0110011`    | `rd = rs1 << rs2` |
|     lsr     | `0000001` |  -  |  -  | `000`  |  -  |    `0110011`    | `rd = rs1 >> rs2` |

#### I - type инструкции
Формат:

|    imm     |    rs1     |   funct3   |    rd     |  opcode  |
| :--------: | :--------: | :--------: | :-------: | :------: |
| `[31..20]` | `[19..15]` | `[14..12]` | `[11..7]` | `[6..0]` |
|  12 bits   |   5 bits   |   3 bits   |  5 bits   |  7 bits  |

Инструкции и их бинарное представление:

| instruction | imm | rs1 | funct3 | rd  |       opcode       |               description               |
| :---------: | :-: | :-: | :----: | :-: | :----------------: | :-------------------------------------: |
|    addi     |  -  |  -  | `000`  |  -  | `0010011  - 0x13`  |            `rd = rs1 + imm`             |
|    andi     |  -  |  -  | `001`  |  -  |  `0010011 - 0x13`  |            `rd = rs1 & imm`             |
|     ori     |  -  |  -  | `010`  |  -  | ``0010011 - 0x13`` |            `rd = rs1 \| imm`            |
|     lw      |  -  |  -  | `000`  |  -  |  `0000011 - 0x3`   |        `rd = mem[rs1 + offset]`         |
|    jalr     |  -  |  -  | `000`  |  -  |  `1100111 - 0x67`  | `PC = (rs1 + offset) & ~1`, `rd = PC+4` |

#### S-type инструкции
Формат:

| imm`[11:5]` |    rs2     |    rs1     |   funct3   | imm`[4:0]` |  opcode  |
| :---------: | :--------: | :--------: | :--------: | :--------: | :------: |
| `[31..25]`  | `[24..20]` | `[19..15]` | `[14..12]` | `[11..7]`  | `[6..0]` |
|   7 bits    |   5 bits   |   5 bits   |   3 bits   |   5 bits   |  7 bits  |

Инструкции и их бинарное представление:

| instruction | imm`[11:5]` | rs2 | rs1 | funct3 | imm`[4:0]` |      opcode      |    description     |
| :---------: | :---------: | :-: | :-: | :----: | :--------: | :--------------: | :----------------: |
|     sw      |      -      |  -  |  -  |  000   |     -      | `0100011 - 0x23` | `[r1 + imm] <- r2` |

#### B-type инструкции
Формат:

| imm`[11:0]` |    rs2     |    rs1     |  funct3  |  opcode  |
| :---------: | :--------: | :--------: | :------: | :------: |
| `[31..21]`  | `[19..15]` | `[14..10]` | `[9..7]` | `[6..0]` |
|   12 bits   |   5 bits   |   5 bits   |  3 bits  |  7 bits  |

Инструкции и их бинарное представление:

| instruction | imm`[11:0]` | rs2 | rs1 | funct3 |      opcode      |             description             |
| ----------- | :---------: | :-: | :-: | :----: | :--------------: | :---------------------------------: |
| beq         |      -      |  -  |  -  | `000`  | `1100011 - 0x63` | `branch if r1 == r2, PC ← PC + imm` |
| bne         |      -      |  -  |  -  | `001`  | `1100011 - 0x63` | `branch if r1 ≠ r2, PC ← PC + imm`  |
| bgt         |      -      |  -  |  -  | `010`  | `1100011 - 0x63` | `branch if r1 > r2, PC ← PC + imm`  |
| ble         |      -      |  -  |  -  | `011`  | `1100011 - 0x63` | `branch if r1 ≤ r2, PC ← PC + imm`  |

#### U-type инструкции
Формат:

|    imm     |    rd     |  opcode  |
| :--------: | :-------: | :------: |
| `[31..12]` | `[11..7]` | `[6..0]` |
|  20 bits   |  5 bits   |  7 bits  |

Инструкции и их бинарное представление:

| instruction | imm`[31:12]` | rd  |      opcode      |         description          |
| :---------: | :----------: | :-: | :--------------: | :--------------------------: |
|     lui     |      -       |  -  | `0110111 - 0x37` | Load upper immediate to `r1` |

#### J-type инструкции
Формат:

| imm`[31:12]` | rd        | opcode   |
| ------------ | --------- | -------- |
| `[31..12]`   | `[11..7]` | `[6..0]` |
| 20 bits      | 5 bits    | 7 bits   |

Инструкции и их бинарное представление:

| instruction | imm`[31:12]` | rd  |      opcode      |          description           |
| :---------: | :----------: | :-: | :--------------: | :----------------------------: |
|     jal     |      -       |  -  | `1101111 - 0x6F` | `PC ← PC + imm`, `r1 ← PC + 4` |

#### sys-type
Формат
| instruction | operands | opcode (bin) | opcode (hex) |    description     |
| :---------: | :------: | :----------: | :----------: | :----------------: |
|   `halt`    |    –     |  `1111111`   |    `0x7F`    | Custom system/halt |

## Транслятор
## Модель процессора
## Тестирование