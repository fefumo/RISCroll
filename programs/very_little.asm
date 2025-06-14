.data
.org 0x0
val: .word 0xCAFEBABE

.text
.org 0x100
    lui t0, high(val)
    addi t0, t0, low(val)
    lw t1, 0(t0)
    halt
