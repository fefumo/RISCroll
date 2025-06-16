.data
    out_addr: .word 0x2

.text
.org 0x100
    lui t0, high(out_addr)
    addi t0, t0, low(out_addr)
    lw t0, 0(t0)            # t0 = *out_addr

    addi t1, r0, 65 # A
    sw t1, 0(t0)

    lui t2, high(print_B)
    addi t2, t2, low(print_B)
    jalr ra, 0(t2)          # jump to print_B, return address → ra

    addi t1, r0, 67 # C
    sw t1, 0(t0)

    halt

print_B:
    addi t1, r0, 66 # B
    sw t1, 0(t0)
    jalr r0, 0(ra)          # return (no rd needed)
