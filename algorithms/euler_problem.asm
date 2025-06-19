# Euler problem n6
# Find the difference between the sum
# of the squares of the first one hundred
# natural numbers and the square of the sum

# t1 -> output pointer  
# t2 -> input pointer   
# t3 -> limit value     
# s1 -> input N         
# a0 -> loop counter `i`
# s2 -> sum of numbers  
# s3 -> sum of squares  
# s4 -> final result    
# t0 -> temp for `i^2`  


.data
in_addr:    .word 0x1
out_addr:   .word 0x2
limit:      .word 46340   # max N to safely square (46340^2 < 2^31)

.text
.org 0x100

# === Load input and output buffer pointers ===
    lui t2, high(in_addr)
    addi t2, t2, low(in_addr)
    lw t2, 0(t2)          # t2 = input ptr

    lui t1, high(out_addr)
    addi t1, t1, low(out_addr)
    lw t1, 0(t1)          # t1 = output ptr

    lui t3, high(limit)
    addi t3, t3, low(limit)
    lw t3, 0(t3)          # t3 = limit value

# === Read N from input ===
    lw s1, 0(t2)          # s1 = N

# === If N > limit → halt ===
    bgt s1, t3, end

    addi a0, r0, 1        # a0 = i = 1
    addi s2, r0, 0        # s2 = sum of numbers
    addi s3, r0, 0        # s3 = sum of squares

# === Loop: i from 1 to N ===
loop:
    bgt a0, s1, calc      # if i > N → go to calc

    add s2, s2, a0        # s2 += i
    mul t0, a0, a0        # t0 = i^2
    add s3, s3, t0        # s3 += i^2

    addi a0, a0, 1
    jal r0, loop

# === After loop: s2 = sum, s3 = sum of squares ===
calc:
    mul s2, s2, s2        # s2 = (sum)^2
    sub s4, s2, s3        # s4 = (sum)^2 - sum of squares

    sw s4, 0(t1)          # write result to output

end:
    halt
