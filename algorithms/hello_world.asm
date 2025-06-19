# This program outputs 'hello world!'
.data 
out_addr: .word 0x2
buf: .byte 'hello world!\0'

.text
.org 0x100

main:
    # int *t0 = &out_addr;
    lui t0, high(out_addr) 
    addi t0, t0, low(out_addr)
    # int t0 = *t0
    lw t0, 0(t0)

    addi t1, t1, buf # t1 <- &buf
    addi t2, r0, 13 # n = 13


loop:
    lw t3, 0(t1) # read symbol from buf
    sb t3, 0(t0) # output
    addi t2, t2, -1 # n--
    addi t1, t1, 1 # buf++
    bne t2, r0, loop # while t2 != 0

    halt