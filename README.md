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

<r_type_instr>    ::= ("add" | "sub" | "sll" | "slt" | "sltu"
                      | "xor" | "srl" | "sra" | "or" | "and")
                     <reg> "," <reg> "," <reg>

<i_type_instr>    ::= ("addi" | "andi" | "ori" | "xori"
                      | "slti" | "sltiu" | "slli" | "srli" | "srai")
                     <reg> "," <reg> "," <immediate>
                    | ("lw" | "lb" | "lh" | "lbu" | "lhu")
                     <reg> "," <offset> "(" <reg> ")"
                    | ("jalr")
                     <reg> "," <offset> "(" <reg> ")"

<s_type_instr>    ::= ("sw" | "sb" | "sh")
                     <reg> "," <offset> "(" <reg> ")"

<b_type_instr>    ::= ("beq" | "bne" | "blt" | "bge" | "bltu" | "bgeu")
                     <reg> "," <reg> "," <label_ref>

<u_type_instr>    ::= ("lui" | "auipc")
                     <reg> "," <immediate>

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

### Стратегия вычислений
### Области видимости
### Типизация, виды литералов

## Организация памяти
## Система команд
## Транслятор
## Модель процессора
## Тестирование
