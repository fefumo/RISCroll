.data
inp_addr:  .word 0x1
out_addr:  .word 0x2

.text
.org 0x100

# === Load input and output buffer addresses ===
    lui a0, high(inp_addr)
    addi a0, a0, low(inp_addr)
    lw a0, 0(a0)         # a0 = input pointer

    lui a1, high(out_addr)
    addi a1, a1, low(out_addr)
    lw a1, 0(a1)         # a1 = output pointer

# === s0 will be the base address of the array in memory (0x300) ===
    lui s0, 0
    addi s0, s0, 768     # s0 = &array[0] (0x300)

    addi t0, r0, 0       # t0 = index = 0

# === Read numbers from input until r0 ===
read_loop:
    lw t1, 0(a0)         # t1 = *input
    beq t1, r0, read_done

    addi t2, r0, 2       # t2 = 2
    mul t3, t0, t2       # t3 = t0 * 2
    mul t3, t3, t2       # t3 = t0 * 4
    add t4, s0, t3       # t4 = address to store

    sw t1, 0(t4)         # store input in array

    addi t0, t0, 1       # index++
    jal r0, read_loop

read_done:
    addi s1, t0, 0       # s1 = number of elements (N)
    addi s2, r0, 0       # s2 = i = 0

# === Outer loop: for i in 0..N-1 ===
outer_loop:
    addi t0, s1, -1      # t0 = N - 1
    bgt t0, s2, skip_sort_done  # if t0 > s2 → continue
    jal r0, sort_done

skip_sort_done:
    addi s3, r0, 0       # s3 = j = 0

# === Inner loop: for j in 0..N-i-2 ===
inner_loop:
    sub t1, s1, s2       # t1 = N - i
    addi t1, t1, -1      # t1 = N - i - 1
    bgt t1, s3, skip_inner_done # if t1 > j → continue
    jal r0, inner_done
skip_inner_done:

    # address of arr[j]
    addi t2, r0, 2
    mul t3, s3, t2
    mul t3, t3, t2       # t3 = j * 4
    add t4, s0, t3       # t4 = &arr[j]

    lw s4, 0(t4)         # s4 = arr[j]
    lw s5, 4(t4)         # s5 = arr[j+1]

    bgt s4, s5, do_swap

skip_swap:
    addi s3, s3, 1
    jal r0, inner_loop

do_swap:
    sw s5, 0(t4)
    sw s4, 4(t4)
    jal r0, skip_swap

inner_done:
    addi s2, s2, 1
    jal r0, outer_loop

# === Output the sorted array ===
sort_done:
    addi t0, r0, 0       # t0 = index = 0

write_loop:
    beq t0, s1, halt     # if index == N → halt

    addi t1, r0, 2
    mul t2, t0, t1
    mul t2, t2, t1       # t2 = t0 * 4
    add t3, s0, t2       # t3 = &arr[index]

    lw t4, 0(t3)
    sw t4, 0(a1)

    addi t0, t0, 1
    jal r0, write_loop

halt:
    halt
