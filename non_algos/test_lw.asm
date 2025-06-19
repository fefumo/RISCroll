.data
inp_addr: .word 0x1
out_addr: .word 0x2

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

    lw t1, 0(a1) # read word
    sw t1, 0(a2) #output
    
    #repeat
    lw t1, 0(a1)
    sw t1, 0(a2)
    halt