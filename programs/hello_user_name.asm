.data
    in_addr:    .word 0x1
    out_addr:   .word 0x2
    
    question:   .byte "What is your name? \0"
    buf:        .byte "Hello, \0"

.text
.org 0x100
    # a1 = *in_addr
    lui a1, high(in_addr)
    addi a1, a1, low(in_addr)
    lw a1, 0(a1)

    # a2 = *out_addr
    lui a2, high(out_addr)
    addi a2, a2, low(out_addr)
    lw a2, 0(a2)

    # a3 = &question
    lui a3, high(question)
    addi a3, a3, low(question)

    # gp = &buf
    lui gp, high(buf)
    addi gp, gp, low(buf)

    # skip past "Hello, "
    addi t0, gp, 0

skip_hello:
    lb t1, 0(t0)
    beq t1, r0, read_input
    addi t0, t0, 1
    jal r0, skip_hello

read_input:
    # t0 — current write ptr (end of "Hello, ")
read_loop:
    lb t1, 0(a1)         # read char
    beq t1, r0, input_done
    sw t1, 0(t0)
    addi t0, t0, 1
    jal r0, read_loop

input_done:
    addi t1, r0, 33      # '!'
    sw t1, 0(t0)
    addi t0, t0, 1
    addi t1, r0, 0       # null terminator
    sw t1, 0(t0)

    addi a0, a3, 0       # a0 = &question
    addi t6, a2, 0       # t6 = out ptr
    jal ra, print_cstr

    addi t1, r0, 10      # '\n'
    sw t1, 0(a2)

    addi a0, gp, 0       # a0 = &buf ("Hello, <name>!\0")
    jal ra, print_cstr

    jal r0, end

# a0 = string ptr, t6 = output ptr
print_cstr:
    addi t0, a0, 0
print_loop:
    lb t1, 0(t0)
    beq t1, r0, print_ret
    sw t1, 0(t6)
    addi t0, t0, 1
    jal r0, print_loop

print_ret:
    jalr r0, ra, 0

end:
    halt
