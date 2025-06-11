"""Instruction Set Architecture of RISCroll"""
INSTRUCTION_SET = {
    "add":  {"type": "R", "opcode": 0x33, "funct3": 0b000, "funct7": 0b0000000},
    "sub":  {"type": "R", "opcode": 0x33, "funct3": 0b001, "funct7": 0b0000000},
    "and":  {"type": "R", "opcode": 0x33, "funct3": 0b010, "funct7": 0b0000000},
    "or":   {"type": "R", "opcode": 0x33, "funct3": 0b011, "funct7": 0b0000000},
    "xor":  {"type": "R", "opcode": 0x33, "funct3": 0b100, "funct7": 0b0000000},
    "mul":  {"type": "R", "opcode": 0x33, "funct3": 0b101, "funct7": 0b0000000},
    "div":  {"type": "R", "opcode": 0x33, "funct3": 0b110, "funct7": 0b0000000},
    "lsl":  {"type": "R", "opcode": 0x33, "funct3": 0b111, "funct7": 0b0000000},
    "lsr":  {"type": "R", "opcode": 0x33, "funct3": 0b000, "funct7": 0b0000001},

    
    "addi": {"type": "I", "opcode": 0x13, "funct3": 0b000},
    "andi": {"type": "I", "opcode": 0x13, "funct3": 0b001},
    "lw":   {"type": "I", "opcode": 0x3,  "funct3": 0b000},
    "jalr": {"type": "I", "opcode": 0x67, "funct3": 0b000},
    
    "sw": {"type": "S", "opcode": 0x23, "funct3": 0b000},
    
    "beq":  {"type": "B", "opcode": 0x63, "funct3": 0b000},
    "bne":  {"type": "B", "opcode": 0x63, "funct3": 0b001},
    "bgt":  {"type": "B", "opcode": 0x63, "funct3": 0b010},
    "ble":  {"type": "B", "opcode": 0x63, "funct3": 0b011},

    "lui":  {"type": "U", "opcode": 0x37},
    
    "jal":  {"type": "J", "opcode": 0x6F},
    "halt": {"type": "SYS", "opcode": 0x7F},
}
