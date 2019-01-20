#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Intel 8080 CPU emulator
# (C) Stanislav Yudin (CityAceE)
# http://zx-pk.ru

import spyc_keyboard

memory = memoryview(bytearray(65536))

ticks = 0  # Ticks number since interrupt
pc = 0  # Program counter
sp = 0  # Stack pointer

regfile = bytearray(8)
regfile_mv = memoryview(regfile)
reg_b = regfile_mv[1:2]
reg_c = regfile_mv[0:1]
reg_d = regfile_mv[3:4]
reg_e = regfile_mv[2:3]
reg_h = regfile_mv[5:6]
reg_l = regfile_mv[4:5]
reg_f = regfile_mv[7:8]
reg_a = regfile_mv[6:7]

reg_bc = regfile_mv[0:2].cast('H')
reg_de = regfile_mv[2:4].cast('H')
reg_hl = regfile_mv[4:6].cast('H')
reg_af = regfile_mv[6:8].cast('H')

reg_list = memoryview(regfile)
rp_list = memoryview(regfile).cast('H')

# Flags
flag_c = False  # 0 carry
flag_p = False  # 2 parity
flag_h = False  # 4 half-carry
flag_z = False  # 6 zero
flag_s = False  # 7 sign

# Parity table for parity flag setting
p_table = [False] * 256
for i in range(256):
    p = True
    for j in range(8):
        if (i & (1 << j)) != 0:
            p = not p
    p_table[i] = p

h_table = (False, False, True, False, True, False, True, True)
sub_h_table = (False, True, True, True, False, False, False, True)


def write_mem(addr, byte):
    # Write one byte to memory address
    # ROM write blocking and memory mapping here

    # Specialist ROM block writing
    if addr < 0xc000:
        memory[addr] = byte

    # Specialist keyboard ports writing
    if 0xf7ff < addr <= 0xffff:
        spyc_keyboard.write_kb_ports(addr, byte)


def read_mem(addr):
    # Read one byte from memory address
    # Configure memory mapping here

    # Specialist keyboard ports reading
    if addr < 0xf800:
        return memory[addr]
    else:
        return spyc_keyboard.read_kb_ports(addr)


def write_port(port, byte):
    # Write one byte to XXXX port
    print('Send %s to %s port' % (hex(byte), hex(port)))
    return


def read_port(port):
    # Read one byte from XXXX port
    print('Read %s port' % hex(port))
    return 0


def flags2f():
    # Pack flags into F register
    if flag_c:
        reg_f[0] = reg_f[0] | 0b00000001
    else:
        reg_f[0] = reg_f[0] & 0b11111110
    if flag_p:
        reg_f[0] = reg_f[0] | 0b00000100
    else:
        reg_f[0] = reg_f[0] & 0b11111011
    if flag_h:
        reg_f[0] = reg_f[0] | 0b00010000
    else:
        reg_f[0] = reg_f[0] & 0b11101111
    if flag_z:
        reg_f[0] = reg_f[0] | 0b01000000
    else:
        reg_f[0] = reg_f[0] & 0b10111111
    if flag_s:
        reg_f[0] = reg_f[0] | 0b10000000
    else:
        reg_f[0] = reg_f[0] & 0b01111111
    reg_f[0] = reg_f[0] & 0b11010111 | 0b00000010  # Flags n, 3 & 5


def f2flags():
    # F register to separate flags
    global flag_c, flag_p, flag_h, flag_z, flag_s
    flag_c = bool(reg_f[0] & 0b00000001)
    flag_p = bool(reg_f[0] & 0b00000100)
    flag_h = bool(reg_f[0] & 0b00010000)
    flag_z = bool(reg_f[0] & 0b01000000)
    flag_s = bool(reg_f[0] & 0b10000000)


def dec2hex16(data):
    # Dec to hex visual converter: 0 -> #0000
    return ('%4s' % str(hex(data))[2:]).replace(' ', '0').upper()


def dec2hex8(data):
    # Dec to hex visual converter: 0 -> #00
    if data is None:
        data = 255
    return ('%2s' % str(hex(data))[2:]).replace(' ', '0').upper()


def disp4b(data):
    # Display four bytes in HEX: 00 00 00 00
    return '%s %s %s %s' % (dec2hex8(read_mem(data % 0x10000)), dec2hex8(read_mem((data + 1) % 0x10000)),
                            dec2hex8(read_mem((data + 2) % 0x10000)), dec2hex8(read_mem((data + 3) % 0x10000)))


def display_regs():
    # Display all registers
    flags2f()
    af = reg_a[0] * 256 + reg_f[0]
    print('AF:', dec2hex16(af), disp4b(af), '\t C =', int(flag_c))
    print('BC:', dec2hex16(reg_bc[0]), disp4b(reg_bc[0]), '\t Z =', int(flag_z))
    print('DE:', dec2hex16(reg_de[0]), disp4b(reg_de[0]), '\t P =', int(flag_p))
    print('HL:', dec2hex16(reg_hl[0]), disp4b(reg_hl[0]), '\t S =', int(flag_s))
    print('SP:', dec2hex16(sp), disp4b(sp), '\tAC =', int(flag_h))
    print('PC:', dec2hex16(pc), disp4b(pc))
    print()


def get_conditions(n):
    return [flag_z, flag_c, flag_p, flag_s][n]


def byte_signed(a):
    # From 32int to signed 8byte
    return (a > 127) and (a - 256) or a


def and_a(reg):
    global reg_a, flag_p, flag_h, flag_c, flag_z, flag_s
    flag_h = bool((reg_a[0] | reg) & 0x08)
    reg_a[0] &= reg
    flag_s = bool(reg_a[0] & 0b10000000)
    flag_z = not reg_a[0]
    flag_p = p_table[reg_a[0]]
    flag_c = False
    return


def xor_a(reg):
    global reg_a, flag_p, flag_h, flag_c, flag_z, flag_s
    reg_a[0] ^= reg
    flag_s = bool(reg_a[0] & 0b10000000)
    flag_z = not reg_a[0]
    flag_h = False
    flag_p = p_table[reg_a[0]]
    flag_c = False
    return


def or_a(reg):
    global reg_a, flag_p, flag_h, flag_c, flag_z, flag_s
    reg_a[0] |= reg
    flag_s = bool(reg_a[0] & 0b10000000)
    flag_z = not reg_a[0]
    flag_h = False
    flag_p = p_table[reg_a[0]]
    flag_c = False
    return


def cp_a(reg):
    global reg_a, flag_p, flag_h, flag_c, flag_z, flag_s
    reg_temp = reg_a[0] - reg
    index = ((reg_a[0] & 0x88) >> 1) | ((reg & 0x88) >> 2) | ((reg_temp & 0x88) >> 3)
    flag_s = bool(reg_temp & 0b10000000)
    flag_z = not (reg_temp % 0x100)
    flag_h = not sub_h_table[index & 0x7]
    flag_c = bool(reg_temp & 0x100)
    flag_p = p_table[reg_temp % 0x100]
    return


def add_a(reg):
    global reg_a, flag_p, flag_h, flag_c, flag_z, flag_s
    reg_temp = reg_a[0] + reg
    index = ((reg_a[0] & 0x88) >> 1) | ((reg & 0x88) >> 2) | ((reg_temp & 0x88) >> 3)
    reg_a[0] = reg_temp % 0x100
    flag_s = bool(reg_a[0] & 0b10000000)
    flag_z = not reg_a[0]
    flag_h = h_table[index & 0x7]
    flag_p = p_table[reg_a[0]]
    flag_c = bool(reg_temp & 0x100)
    return


def adc_a(reg):
    global reg_a, flag_p, flag_h, flag_c, flag_z, flag_s
    reg_temp = reg_a[0] + reg + flag_c
    index = ((reg_a[0] & 0x88) >> 1) | ((reg & 0x88) >> 2) | ((reg_temp & 0x88) >> 3)
    reg_a[0] = reg_temp % 0x100
    flag_s = bool(reg_a[0] & 0b10000000)
    flag_z = not reg_a[0]
    flag_h = h_table[index & 0x7]
    flag_p = p_table[reg_a[0]]
    flag_c = bool(reg_temp & 0x100)
    return


def sub_a(reg):
    global reg_a, flag_p, flag_h, flag_c, flag_z, flag_s
    reg_temp = reg_a[0] - reg
    index = ((reg_a[0] & 0x88) >> 1) | ((reg & 0x88) >> 2) | ((reg_temp & 0x88) >> 3)
    reg_a[0] = reg_temp % 0x100
    flag_s = bool(reg_a[0] & 0b10000000)
    flag_z = not reg_a[0]
    flag_h = not sub_h_table[index & 0x7]
    flag_p = p_table[reg_a[0]]
    flag_c = bool(reg_temp & 0x100)
    return


def sbc_a(reg):
    global reg_a, flag_p, flag_h, flag_c, flag_z, flag_s
    reg_temp = reg_a[0] - reg - flag_c
    index = ((reg_a[0] & 0x88) >> 1) | ((reg & 0x88) >> 2) | ((reg_temp & 0x88) >> 3)
    reg_a[0] = reg_temp % 0x100
    flag_s = bool(reg_a[0] & 0b10000000)
    flag_z = not reg_a[0]
    flag_h = not sub_h_table[index & 0x7]
    flag_p = p_table[reg_a[0]]
    flag_c = bool(reg_temp & 0x100)
    return


def inc_pc(inc=1):
    # PC increment
    return (pc + inc) % 0x10000


def inc_reg(reg):
    global flag_p, flag_h, flag_z, flag_s
    reg = (reg + 1) % 0x100
    flag_s = bool(reg & 0b10000000)
    flag_z = not reg
    flag_h = not (reg % 0x10)
    flag_p = p_table[reg]
    return reg


def dec_reg(reg):
    global flag_p, flag_h, flag_z, flag_s
    reg = (reg - 1) % 0x100
    flag_s = bool(reg & 0b10000000)
    flag_z = not reg
    flag_h = not (reg % 0x10 == 0x0f)
    flag_p = p_table[reg]
    return reg


# CPU instructions set emulation

# 00 XXX XXX opcodes group

def b00000000():  # NOP / NOP
    global pc, ticks
    pc = inc_pc()
    ticks += 4
    return


def b00000001():  # LD RP,nn / LXI R,nn
    global pc, ticks
    rp_list[(opcode & 0b110000) >> 4] = read_mem(inc_pc()) + read_mem(inc_pc(2)) * 256

    pc = inc_pc(3)
    ticks += 10
    return


def b00110001():  # LD SP,nn / LXI SP,nn
    global pc, ticks, sp
    sp = read_mem(inc_pc(2)) * 256 + read_mem(inc_pc())
    pc = inc_pc(3)
    ticks += 10
    return


def b00001001():  # ADD HL,RP / DAD R
    global pc, ticks, flag_c
    reg_temp = reg_hl[0] + rp_list[(opcode & 0b110000) >> 4]
    flag_c = bool(reg_temp & 0x10000)
    reg_hl[0] = reg_temp % 0x10000
    pc = inc_pc()
    ticks += 10
    return


def b00111001():  # ADD HL,SP / DAD SP
    global pc, ticks, flag_c
    reg_temp = reg_hl[0] + sp
    flag_c = bool(reg_temp & 0x10000)
    reg_hl[0] = reg_temp % 0x10000
    pc = inc_pc()
    ticks += 10
    return


def b00010010():  # LD (DE),A / STAX D
    global pc, ticks
    write_mem(reg_de[0], reg_a[0])
    pc = inc_pc()
    ticks += 7
    return


def b00000010():  # LD (BC),A / STAX B
    global pc, ticks
    write_mem(reg_bc[0], reg_a[0])
    pc = inc_pc()
    ticks += 7
    return


def b00011010():  # LD A,(DE) / LDAX D
    global pc, ticks
    reg_a[0] = read_mem(reg_de[0])
    pc = inc_pc()
    ticks += 7
    return


def b00001010():  # LD A,(BC) / LDAX B
    global pc, ticks
    reg_a[0] = read_mem(reg_bc[0])
    pc = inc_pc()
    ticks += 7
    return


def b00100010():  # LD (nn),HL / SHLD nn
    global pc, ticks
    write_mem(read_mem(inc_pc(2)) * 256 + read_mem(inc_pc()), reg_l[0])
    write_mem((read_mem(inc_pc(2)) * 256 + read_mem(inc_pc()) + 1) % 0x10000, reg_h[0])
    pc = inc_pc(3)
    ticks += 16
    return


def b00101010():  # LD HL,(nn) / LHLD nn
    global pc, ticks
    reg_l[0] = read_mem(read_mem(inc_pc(2)) * 256 + read_mem(inc_pc()))
    reg_h[0] = read_mem((read_mem(inc_pc(2)) * 256 + read_mem(inc_pc()) + 1) % 0x10000)
    pc = inc_pc(3)
    ticks += 16
    return


def b00110010():  # LD (nn),A / STA nn
    global pc, ticks
    write_mem(read_mem(inc_pc(2)) * 256 + read_mem(inc_pc()), reg_a[0])
    pc = inc_pc(3)
    ticks += 13
    return


def b00111010():  # LD A,(nn) / LDA nn
    global pc, ticks
    reg_a[0] = read_mem(read_mem(inc_pc(2)) * 256 + read_mem(inc_pc()))
    pc = inc_pc(3)
    ticks += 13
    return


def b00000011():  # INC RP / INX R
    global pc, ticks
    index = (opcode & 0b110000) >> 4
    rp_list[index] = (rp_list[index] + 1) % 0x10000
    pc = inc_pc()
    ticks += 5
    return


def b00110011():  # INC SP / INX SP
    global pc, ticks, sp
    sp = (sp + 1) % 0x10000
    pc = inc_pc()
    ticks += 5
    return


def b00001011():  # DEC RP / DCX R
    global pc, ticks
    index = (opcode & 0b110000) >> 4
    rp_list[index] = (rp_list[index] - 1) % 0x10000
    pc = inc_pc()
    ticks += 6
    return


def b00111011():  # DEC SP / DCX SP
    global pc, ticks, sp
    sp = (sp - 1) % 0x10000
    pc = inc_pc()
    ticks += 6
    return


def b00110100():  # INC (HL) / INR M
    global pc, ticks
    write_mem(reg_hl[0], inc_reg(read_mem(reg_hl[0])))
    ticks += 10
    pc = inc_pc()
    return


def b00000100():  # INC SSS / INR S
    global pc, ticks
    index = 1 ^ (opcode % 0b1000000) >> 3
    reg_list[index] = inc_reg(reg_list[index])
    ticks += 5
    pc = inc_pc()
    return


def b00110101():  # DEC (HL) / DCR M
    global pc, ticks
    write_mem(reg_hl[0], dec_reg(read_mem(reg_hl[0])))
    ticks += 10
    pc = inc_pc()
    return


def b00000101():  # DEC SSS / DCR S
    global pc, ticks
    index = 1 ^ (opcode % 0b1000000) >> 3
    reg_list[index] = dec_reg(reg_list[index])
    ticks += 5
    pc = inc_pc()
    return


def b00110110():  # LD (HL),d / MVI M,d
    global pc, ticks
    write_mem(reg_h[0] * 256 + reg_l[0], read_mem(inc_pc()))
    ticks += 10
    pc = inc_pc(2)
    return


def b00000110():  # LD DDD,d / MVI D,d
    global pc, ticks
    index = 1 ^ (opcode % 0b1000000) >> 3
    reg_list[index] = read_mem(inc_pc())
    ticks += 7
    pc = inc_pc(2)
    return


def b00000111():  # RLCA / RLC
    global pc, ticks, flag_c
    reg_temp = reg_a[0]
    reg_temp = reg_temp << 1
    flag_c = bool(reg_temp & 0x100)
    reg_a[0] = (reg_temp | flag_c) % 0x100
    pc = inc_pc()
    ticks += 4
    return


def b00001111():  # RRCA / RRC
    global pc, ticks, flag_c
    flag_temp = bool(reg_a[0] & 1)
    reg_a[0] = reg_a[0] >> 1 | (reg_a[0] & 1) << 7
    flag_c = flag_temp
    pc = inc_pc()
    ticks += 4
    return


def b00010111():  # RLA / RAL
    global pc, ticks, flag_c
    reg_temp = reg_a[0]
    reg_temp = reg_temp << 1 | flag_c
    flag_c = bool(reg_temp & 0x100)
    reg_a[0] = reg_temp % 0x100
    pc = inc_pc()
    ticks += 4
    return


def b00011111():  # RRA / RAR
    global pc, ticks, flag_c
    flag_temp = bool(reg_a[0] & 1)
    reg_a[0] = reg_a[0] >> 1 | flag_c << 7
    flag_c = flag_temp
    pc = inc_pc()
    ticks += 4
    return


def b00100111():  # DAA / DAA
    global pc, ticks, flag_c
    carry = flag_c
    addition = 0
    if flag_h or ((reg_a[0] % 0x10) > 0x09):
        addition = 0x06
    if flag_c or (reg_a[0] > 0x9f) or ((reg_a[0] > 0x8f) and ((reg_a[0] % 0x10) > 0x09)):
        addition |= 0x60
    if reg_a[0] > 0x99:
        carry = True
    add_a(addition)
    flag_c = carry
    pc = inc_pc()
    ticks += 4
    return


def b00101111():  # CPL / CMA
    global pc, ticks
    reg_a[0] ^= 0xff
    pc = inc_pc()
    ticks += 4
    return


def b00110111():  # SCF / STC
    global pc, ticks, flag_c
    flag_c = True
    pc = inc_pc()
    ticks += 4
    return


def b00111111():  # CCF / CMC
    global pc, ticks, flag_c
    flag_c = not flag_c
    pc = inc_pc()
    ticks += 4
    return


# 01 XXX XXX group

def b01110110():  # HALT / HLT
    global ticks
    ticks += 4
    return


def b01000110():  # LD DDD,(HL) / MOV D,M
    global pc, ticks
    reg_list[1 ^ (opcode % 0b1000000) >> 3] = read_mem(reg_hl[0])
    pc = inc_pc()
    ticks += 7
    return


def b01110000():  # LD (HL),SSS / MOV M,S
    global pc, ticks
    write_mem(reg_hl[0], reg_list[1 ^ (opcode % 0b1000)])
    pc = inc_pc()
    ticks += 7
    return


def b01000000():  # LD DDD,SSS / MOV D,S
    global pc, ticks
    reg_list[1 ^ (opcode % 0b1000000) >> 3] = reg_list[1 ^ (opcode % 0b1000)]
    pc = inc_pc()
    ticks += 5
    return


# 10 XXX XXX group

def b10000110():  # ADD A,(HL) / ADD M
    global pc, ticks
    add_a(read_mem(reg_hl[0]))
    pc = inc_pc()
    ticks += 7
    return


def b10000000():  # ADD A,SSS / ADD S
    global pc, ticks
    add_a(reg_list[1 ^ (opcode % 0b1000)])
    pc = inc_pc()
    ticks += 4
    return


def b10001110():  # ADC A,(HL) / ADC M
    global pc, ticks
    adc_a(read_mem(reg_hl[0]))
    pc = inc_pc()
    ticks += 7
    return


def b10001000():  # ADC A,SSS / ADC S
    global pc, ticks
    adc_a(reg_list[1 ^ (opcode % 0b1000)])
    pc = inc_pc()
    ticks += 4
    return


def b10010110():  # SUB A,(HL) / SUB M
    global pc, ticks
    sub_a(read_mem(reg_hl[0]))
    pc = inc_pc()
    ticks += 7
    return


def b10010000():  # SUB A,SSS / SUB S
    global pc, ticks
    sub_a(reg_list[1 ^ (opcode % 0b1000)])
    pc = inc_pc()
    ticks += 4
    return


def b10011110():  # SBC A,(HL) / SBB M
    global pc, ticks
    sbc_a(read_mem(reg_hl[0]))
    pc = inc_pc()
    ticks += 7
    return


def b10011000():  # SBC A,SSS / SBB S
    global pc, ticks
    sbc_a(reg_list[1 ^ (opcode % 0b1000)])
    pc = inc_pc()
    ticks += 4
    return


def b10100110():  # AND A,(HL) / ANA M
    global pc, ticks
    and_a(read_mem(reg_hl[0]))
    pc = inc_pc()
    ticks += 7
    return


def b10100000():  # AND A,SSS / ANA S
    global pc, ticks
    and_a(reg_list[1 ^ (opcode % 0b1000)])
    pc = inc_pc()
    ticks += 4
    return


def b10101110():  # XOR A,(HL) / XRA M
    global pc, ticks
    xor_a(read_mem(reg_hl[0]))
    pc = inc_pc()
    ticks += 7
    return


def b10101000():  # XOR A,SSS / XRA S
    global pc, ticks
    xor_a(reg_list[1 ^ (opcode % 0b1000)])
    pc = inc_pc()
    ticks += 4
    return


def b10110110():  # OR A,(HL) / ORA M
    global pc, ticks
    or_a(read_mem(reg_hl[0]))
    pc = inc_pc()
    ticks += 7
    return


def b10110000():  # OR A,SSS / ORA S
    global pc, ticks
    or_a(reg_list[1 ^ (opcode % 0b1000)])
    pc = inc_pc()
    ticks += 4
    return


def b10111110():  # CP (HL) / CMP M
    global pc, ticks
    cp_a(read_mem(reg_hl[0]))
    pc = inc_pc()
    ticks += 7
    return


def b10111000():  # CP SSS / CMP S
    global pc, ticks
    cp_a(reg_list[1 ^ (opcode % 0b1000)])
    pc = inc_pc()
    ticks += 4
    return


# 11 XXX XXX group

def b11000000():  # RET CCC / RCCC
    global pc, ticks, sp
    if get_conditions((opcode & 0b110000) >> 4) == bool(opcode & 0b001000):
        pc = read_mem(sp) + read_mem((sp + 1) % 0x10000) * 256
        sp = (sp + 2) % 0x10000
        ticks += 11
        return
    else:
        ticks += 5
        pc = inc_pc()
        return


def b11000001():  # POP RP / POP R
    global pc, ticks, sp
    rp_list[(opcode & 0b110000) >> 4] = read_mem((sp + 1) % 0x10000) * 256 + read_mem(sp)
    sp = (sp + 2) % 0x10000
    ticks += 10
    pc = inc_pc()
    return


def b11110001():  # POP AF / POP PSW
    global pc, ticks, sp
    reg_f[0] = read_mem(sp)
    f2flags()
    reg_a[0] = read_mem((sp + 1) % 0x10000)
    sp = (sp + 2) % 0x10000
    ticks += 10
    pc = inc_pc()
    return


def b11001001():  # RET / RET
    global pc, ticks, sp
    pc = read_mem(sp) + read_mem((sp + 1) % 0x10000) * 256
    sp = (sp + 2) % 0x10000
    ticks += 10
    return


def b11101001():  # JP (HL) / PCHL
    global pc, ticks
    pc = reg_hl[0]
    ticks += 5
    return


def b11111001():  # LD SP,HL / SPHL
    global pc, ticks, sp
    sp = reg_hl[0]
    pc = inc_pc()
    ticks += 5
    return


def b11000010():  # JP CCC,nn / JCCC nn
    global pc, ticks
    if get_conditions((opcode & 0b110000) >> 4) == bool(opcode & 0b001000):
        pc = read_mem(inc_pc()) + read_mem(inc_pc(2)) * 256
        ticks += 10
        return
    else:
        ticks += 10
        pc = inc_pc(3)
        return


def b11000011():  # JP nn / JMP nn
    global pc, ticks
    pc = read_mem(inc_pc()) + read_mem(inc_pc(2)) * 256
    ticks += 10
    return


def b11010011():  # OUT (d),A / OUT d
    global pc, ticks
    write_port(reg_a[0] * 256 + read_mem(inc_pc()), reg_a[0])
    pc = inc_pc(2)
    ticks += 10
    return


def b11011011():  # IN A,(d) / IN d
    global pc, ticks
    reg_a[0] = read_port(reg_a[0] * 256 + read_mem(inc_pc()))
    pc = inc_pc(2)
    ticks += 10
    return


def b11100011():  # EX (SP),HL / XTHL
    global pc, ticks
    reg_templ = read_mem(sp)
    reg_temph = read_mem((sp + 1) % 0x10000)
    write_mem(sp, reg_l[0])
    write_mem((sp + 1) % 0x10000, reg_h[0])
    reg_l[0] = reg_templ
    reg_h[0] = reg_temph
    pc = inc_pc()
    ticks += 18
    return


def b11101011():  # EX DE,HL / XCHG
    global pc, ticks
    reg_de[0], reg_hl[0] = reg_hl[0], reg_de[0]
    pc = inc_pc()
    ticks += 5
    return


def b11110011():  # DI / DI
    global pc, ticks
    pc = inc_pc()
    ticks += 4
    return


def b11111011():  # EI /EI
    global pc, ticks
    pc = inc_pc()
    ticks += 4
    return


def b11000100():  # CALL CCC,nn / CCCC,nn
    global pc, ticks, sp
    reg_temp = inc_pc(3)
    if get_conditions((opcode & 0b110000) >> 4) == bool(opcode & 0b001000):
        sp = (sp - 2) % 0x10000
        write_mem(sp, reg_temp % 256)
        write_mem((sp + 1) % 0x10000, reg_temp // 256)
        pc = read_mem(inc_pc()) + read_mem(inc_pc(2)) * 256
        ticks += 17
        return
    else:
        ticks += 11
        pc = reg_temp
        return


def b11000101():  # PUSH RP / PUSH R
    global pc, ticks, sp
    sp = (sp - 2) % 0x10000
    index = (opcode & 0b110000) >> 4
    write_mem(sp, rp_list[index] % 256)
    write_mem((sp + 1) % 0x10000, rp_list[index] // 256)
    pc = inc_pc()
    ticks += 11
    return


def b11110101():  # PUSH AF / PUSH PSW
    global pc, ticks, sp
    sp = (sp - 2) % 0x10000
    flags2f()
    write_mem(sp, reg_f[0])
    write_mem((sp + 1) % 0x10000, reg_a[0])
    pc = inc_pc()
    ticks += 11
    return


def b11001101():  # CALL nn / CALL nn
    global pc, ticks, sp
    sp = (sp - 2) % 0x10000
    reg_temp = inc_pc(3)
    write_mem(sp, reg_temp % 256)
    write_mem((sp + 1) % 0x10000, reg_temp // 256)
    pc = read_mem(inc_pc()) + read_mem(inc_pc(2)) * 256
    ticks += 17
    return


def b11000110():  # ADD A,d / ADI d
    global pc, ticks
    add_a(read_mem(inc_pc()))
    pc = inc_pc(2)
    ticks += 7
    return


def b11001110():  # ADC A,d / ACI d
    global pc, ticks
    adc_a(read_mem(inc_pc()))
    pc = inc_pc(2)
    ticks += 7
    return


def b11010110():  # SUB A,d / SUI d
    global pc, ticks
    sub_a(read_mem(inc_pc()))
    pc = inc_pc(2)
    ticks += 7
    return


def b11011110():  # SBC A,d / SBI d
    global pc, ticks
    sbc_a(read_mem(inc_pc()))
    pc = inc_pc(2)
    ticks += 7
    return


def b11100110():  # AND A,d / ANI d
    global pc, ticks
    and_a(read_mem(inc_pc()))
    pc = inc_pc(2)
    ticks += 7
    return


def b11101110():  # XOR A,d / XRI d
    global pc, ticks
    xor_a(read_mem(inc_pc()))
    pc = inc_pc(2)
    ticks += 7
    return


def b11110110():  # OR A,d / ORI d
    global pc, ticks
    or_a(read_mem(inc_pc()))
    pc = inc_pc(2)
    ticks += 7
    return


def b11111110():  # CP A,d / CPI d
    global pc, ticks
    cp_a(read_mem(inc_pc()))
    pc = inc_pc(2)
    ticks += 7
    return


def b11000111():  # RST N / RST N
    global pc, ticks, sp
    sp = (sp - 2) % 0x10000
    reg_temp = inc_pc()
    write_mem(sp, reg_temp % 256)
    write_mem((sp + 1) % 0x10000, reg_temp // 256)
    pc = ((opcode & 0b00111000) >> 3) * 8
    ticks += 11
    return


opcodes = {0x00: b00000000, 0x08: b00000000, 0x10: b00000000, 0x18: b00000000,
           0x20: b00000000, 0x28: b00000000, 0x30: b00000000, 0x38: b00000000,
           0x01: b00000001, 0x11: b00000001, 0x21: b00000001, 0x31: b00110001,
           0x09: b00001001, 0x19: b00001001, 0x29: b00001001, 0x39: b00111001,
           0x02: b00000010, 0x12: b00010010, 0x0A: b00001010, 0x1A: b00011010,
           0x22: b00100010, 0x2A: b00101010, 0x32: b00110010, 0x3A: b00111010,
           0x03: b00000011, 0x13: b00000011, 0x23: b00000011, 0x33: b00110011,
           0x0B: b00001011, 0x1B: b00001011, 0x2B: b00001011, 0x3B: b00111011,
           0x04: b00000100, 0x0C: b00000100, 0x14: b00000100, 0x1C: b00000100,
           0x24: b00000100, 0x2C: b00000100, 0x34: b00110100, 0x3C: b00000100,
           0x05: b00000101, 0x0D: b00000101, 0x15: b00000101, 0x1D: b00000101,
           0x25: b00000101, 0x2D: b00000101, 0x35: b00110101, 0x3D: b00000101,
           0x06: b00000110, 0x0E: b00000110, 0x16: b00000110, 0x1E: b00000110,
           0x26: b00000110, 0x2E: b00000110, 0x36: b00110110, 0x3E: b00000110,
           0x07: b00000111, 0x0F: b00001111, 0x17: b00010111, 0x1F: b00011111,
           0x27: b00100111, 0x2F: b00101111, 0x37: b00110111, 0x3F: b00111111,

           0x76: b01110110, 0x46: b01000110, 0x4E: b01000110, 0x56: b01000110,
           0x5E: b01000110, 0x66: b01000110, 0x6E: b01000110, 0x7E: b01000110,
           0x70: b01110000, 0x71: b01110000, 0x72: b01110000, 0x73: b01110000,
           0x74: b01110000, 0x75: b01110000, 0x77: b01110000, 0x40: b01000000,
           0x41: b01000000, 0x42: b01000000, 0x43: b01000000, 0x44: b01000000,
           0x45: b01000000, 0x47: b01000000, 0x48: b01000000, 0x49: b01000000,
           0x4A: b01000000, 0x4B: b01000000, 0x4C: b01000000, 0x4D: b01000000,
           0x4F: b01000000, 0x50: b01000000, 0x51: b01000000, 0x52: b01000000,
           0x53: b01000000, 0x54: b01000000, 0x55: b01000000, 0x57: b01000000,
           0x58: b01000000, 0x59: b01000000, 0x5A: b01000000, 0x5B: b01000000,
           0x5C: b01000000, 0x5D: b01000000, 0x5F: b01000000, 0x60: b01000000,
           0x61: b01000000, 0x62: b01000000, 0x63: b01000000, 0x64: b01000000,
           0x65: b01000000, 0x67: b01000000, 0x68: b01000000, 0x69: b01000000,
           0x6A: b01000000, 0x6B: b01000000, 0x6C: b01000000, 0x6D: b01000000,
           0x6F: b01000000, 0x78: b01000000, 0x79: b01000000, 0x7A: b01000000,
           0x7B: b01000000, 0x7C: b01000000, 0x7D: b01000000, 0x7F: b01000000,

           0x80: b10000000, 0x81: b10000000, 0x82: b10000000, 0x83: b10000000,
           0x84: b10000000, 0x85: b10000000, 0x86: b10000110, 0x87: b10000000,
           0x88: b10001000, 0x89: b10001000, 0x8A: b10001000, 0x8B: b10001000,
           0x8C: b10001000, 0x8D: b10001000, 0x8E: b10001110, 0x8F: b10001000,
           0x90: b10010000, 0x91: b10010000, 0x92: b10010000, 0x93: b10010000,
           0x94: b10010000, 0x95: b10010000, 0x96: b10010110, 0x97: b10010000,
           0x98: b10011000, 0x99: b10011000, 0x9A: b10011000, 0x9B: b10011000,
           0x9C: b10011000, 0x9D: b10011000, 0x9E: b10011110, 0x9F: b10011000,
           0xA0: b10100000, 0xA1: b10100000, 0xA2: b10100000, 0xA3: b10100000,
           0xA4: b10100000, 0xA5: b10100000, 0xA6: b10100110, 0xA7: b10100000,
           0xA8: b10101000, 0xA9: b10101000, 0xAA: b10101000, 0xAB: b10101000,
           0xAC: b10101000, 0xAD: b10101000, 0xAE: b10101110, 0xAF: b10101000,
           0xB0: b10110000, 0xB1: b10110000, 0xB2: b10110000, 0xB3: b10110000,
           0xB4: b10110000, 0xB5: b10110000, 0xB6: b10110110, 0xB7: b10110000,
           0xB8: b10111000, 0xB9: b10111000, 0xBA: b10111000, 0xBB: b10111000,
           0xBC: b10111000, 0xBD: b10111000, 0xBE: b10111110, 0xBF: b10111000,

           0xC0: b11000000, 0xC8: b11000000, 0xD0: b11000000, 0xD8: b11000000,
           0xE0: b11000000, 0xE8: b11000000, 0xF0: b11000000, 0xF8: b11000000,
           0xC1: b11000001, 0xD1: b11000001, 0xE1: b11000001, 0xF1: b11110001,
           0xC9: b11001001, 0xD9: b11001001, 0xE9: b11101001, 0xF9: b11111001,
           0xC2: b11000010, 0xCA: b11000010, 0xD2: b11000010, 0xDA: b11000010,
           0xE2: b11000010, 0xEA: b11000010, 0xF2: b11000010, 0xFA: b11000010,
           0xC3: b11000011, 0xCB: b11000011, 0xD3: b11010011, 0xDB: b11011011,
           0xE3: b11100011, 0xEB: b11101011, 0xF3: b11110011, 0xFB: b11111011,
           0xC4: b11000100, 0xCC: b11000100, 0xD4: b11000100, 0xDC: b11000100,
           0xE4: b11000100, 0xEC: b11000100, 0xF4: b11000100, 0xFC: b11000100,
           0xC5: b11000101, 0xD5: b11000101, 0xE5: b11000101, 0xF5: b11110101,
           0xCD: b11001101, 0xDD: b11001101, 0xED: b11001101, 0xFD: b11001101,
           0xC6: b11000110, 0xCE: b11001110, 0xD6: b11010110, 0xDE: b11011110,
           0xE6: b11100110, 0xEE: b11101110, 0xF6: b11110110, 0xFE: b11111110,
           0xC7: b11000111, 0xCF: b11000111, 0xD7: b11000111, 0xDF: b11000111,
           0xE7: b11000111, 0xEF: b11000111, 0xF7: b11000111, 0xFF: b11000111}


def core():
    global opcode
    opcode = memory[pc]
    return opcodes[opcode]()


def fill_memory(codes):
    # Fill memory by codes
    i = 0
    for code in codes:
        memory[(pc + i) % 0x10000] = code
        i += 1


if __name__ == '__main__':
    # For debugging CPU emulation
    pc = 0x8000
    sp = 0x8ede

    flag_c = True
    # flag_p = True
    # flag_h = True
    # flag_z = True
    # flag_s = True

    reg_a[0] = 0x00
    reg_b[0] = 0x00
    reg_c[0] = 0x00
    reg_d[0] = 0x00
    reg_e[0] = 0x00
    reg_h[0] = 0x00
    reg_l[0] = 0x00

    fill_memory([0x21, 0x00, 0xf8, 0x00])

    display_regs()
    core()
    display_regs()
