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

    # Read a character from input (from address stored in t1)
    lw t2, 0(t1)          # t2 = *0x1

    # Load out_addr into t3
    lui t3, high(out_addr)
    addi t3, t3, low(out_addr)
    lw t4, 0(t3)          # t4 = *out_addr (== 0x2)

    # Write character to output (to address stored in t4)
    sb t2, 0(t4)

    halt
