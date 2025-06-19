.data
out_addr: .word 0x2
msg: .byte 'Hello, this is macro_showcase!\0'

.text
.org 0x100

.macro load_addr reg, label
    lui \reg, high(\label)
    addi \reg, \reg, low(\label)
    lw \reg, 0(\reg)
.endmacro

start:
    addi t1, t1, msg # t1 <- &msg
    load_addr t2, out_addr

print_loop:
    lb t3, 0(t1) # read symbol from buf
    sb t3, 0(t2) # output
    addi t1, t1, 1 # msg++
    bne t3, r0, print_loop # while t1 != 0

end:
    halt
