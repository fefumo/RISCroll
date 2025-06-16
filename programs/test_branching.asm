.data
    out_addr: .word 0x2

.text
.org 0x100

main:
    addi t2, t2, 2

kekw:
    lui t1, high(branch)
    addi t1, t1, low(branch)

branch:
    bne t2, r0, fuck
    halt

fuck:
    addi t2, t2, -1
    jal r0, branch
