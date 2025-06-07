# RISCroll
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

<value>           ::= <identifier> | <number> | <string>

<string>          ::= '"' { <any_char_except_quote> } '"'

<instruction>     ::= <r_type_instr>
                        | <i_type_instr>
                        | <s_type_instr>
                        | <b_type_instr>
                        | <u_type_instr>
                        | <j_type_instr>
                        | <sys_instr>

<r_type_instr>    ::= ("add" | "sub" | "slt" | "and" | "or" | "xor")
                     <reg> "," <reg> "," <reg>

<i_type_instr>    ::= ("addi" | "andi") <reg> "," <reg> "," <immediate>
                        | ("lw" | "lb") <reg> "," <offset> "(" <reg> ")"
                        | ("jalr") <reg> "," <offset> "(" <reg> ")"

<s_type_instr>    ::= ("sw" | "sb") <reg> "," <offset> "(" <reg> ")"

<b_type_instr>    ::= ("beq" | "bne" | "blt" | "bge")  <reg> "," <reg> "," <label_ref>

<u_type_instr>    ::= ("lui" | "auipc") <reg> "," <immediate>

<sys_instr>       ::= "halt"

<j_type_instr>    ::= "jal" <reg> "," <label_ref>

<comment>         ::= "#" { <any_char_except_newline> }

<reg>             ::= "$r" <number>         // $r0 to $r31

<offset>          ::= <number>
<immediate>       ::= <number>
<label_ref>       ::= <identifier>

<identifier>      ::= <letter> { <letter> | <digit> | "_" }
<number>          ::= ["-"] <digit> { <digit> }

<letter>          ::= "A" | ... | "Z" | "a" | ... | "z"
<digit>           ::= "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9"

<macro_def> ::= ".macro" <identifier> [<macro_param_list>] <newline>
                { <line> }
                ".endm" <newline>

<macro_param_list> ::= <identifier> { "," <identifier> }

<macro_use> ::= <identifier> [<macro_arg_list>]

<macro_arg_list> ::= <value> { "," <value> }

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
### Области видимости
### Типизация, виды литералов

## Организация памяти
## Система команд
## Транслятор
## Модель процессора
## Тестирование
