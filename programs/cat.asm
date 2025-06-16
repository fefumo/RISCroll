.data
.org 0x0
inp_addr:  .word 0x1      # input address
out_addr:  .word 0x2      # output address

.text
.org 0x100
    # Load inp_addr into t0
    lui t0, high(inp_addr)
    addi t0, t0, low(inp_addr)
    lw t1, 0(t0)          # t1 = *inp_addr (== 0x1)

    # Load out_addr into t2
    lui t0, high(out_addr)
    addi t0, t0, low(out_addr)
    lw t2, 0(t0)          # t2 = *out_addr (== 0x2)

loop:
    # Read character from input (t1 points to input address)
    lw t3, 0(t1)          # t3 = *0x1 (next char)

    # Write character to output (t2 points to output address)
    sw t3, 0(t2)

    bne t3, r0, loop     # if t3 == 0, break the loop

end:
    halt
