#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Intel 8080 CPU emulator
# (C) Stanislav Yudin (CityAceE)
# http://zx-pk.ru

memory = [0x00 for i in range(65536)]

i8080 = True

# SPECIALIST
vv55a_mode = 0x82
ports_91 = [0xff, 0x00, 0x0f, 0x00]
ports_82 = [0x00, 0xff, 0x00, 0xff]

ticks = 0

pc = 0  # Program counter
sp = 0  # Stack pointer

# Main registers
reg_h = 0
reg_l = 0
reg_e = 0
reg_d = 0
reg_c = 0
reg_b = 0
reg_f = 0
reg_a = 0

# Z80 alternate registers
reg_h_ = 0
reg_l_ = 0
reg_e_ = 0
reg_d_ = 0
reg_c_ = 0
reg_b_ = 0
reg_f_ = 0
reg_a_ = 0

reg_ixh = 0
reg_ixl = 0
reg_iyh = 0
reg_iyl = 0

reg_i = 0  # Interrupt vector
reg_r = 0  # DRAM refresh counter

iff1 = False
iff2 = False

# Flags
flag_c = False  # 0 carry
flag_n = True   # 1 negative
flag_p = False  # 2 parity/overflow
flag_3 = False  # 3
flag_h = False  # 4 half-carry
flag_5 = False  # 5
flag_z = False  # 6 zero
flag_s = False  # 7 sign


def fflag_3(flag):
    global flag_3
    if not i8080:
        flag_3 = flag


def fflag_5(flag):
    global flag_5
    if not i8080:
        flag_5 = flag


def fflag_n(flag):
    global flag_n
    if not i8080:
        flag_n = flag


reg_lst = ('reg_b', 'reg_c', 'reg_d', 'reg_e', 'reg_h', 'reg_l', '', 'reg_a')
reg_pairs = (('reg_b', 'reg_c'), ('reg_d', 'reg_e'), ('reg_h', 'reg_l'))
conditions = ('flag_z', 'flag_c', 'flag_p', 'flag_s')

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


def flags2f():
    # Pack flags into F register
    global reg_f
    if flag_c:
        reg_f = reg_f | 0b00000001
    else:
        reg_f = reg_f & 0b11111110
    if flag_n:
        reg_f = reg_f | 0b00000010
    else:
        reg_f = reg_f & 0b11111101
    if flag_p:
        reg_f = reg_f | 0b00000100
    else:
        reg_f = reg_f & 0b11111011
    if flag_3:
        reg_f = reg_f | 0b00001000
    else:
        reg_f = reg_f & 0b11110111
    if flag_h:
        reg_f = reg_f | 0b00010000
    else:
        reg_f = reg_f & 0b11101111
    if flag_5:
        reg_f = reg_f | 0b00100000
    else:
        reg_f = reg_f & 0b11011111
    if flag_z:
        reg_f = reg_f | 0b01000000
    else:
        reg_f = reg_f & 0b10111111
    if flag_s:
        reg_f = reg_f | 0b10000000
    else:
        reg_f = reg_f & 0b01111111


def f2flags():
    # F register to separate flags
    global flag_c, flag_p, flag_h, flag_z, flag_s
    flag_c = bool(reg_f & 0b00000001)
    fflag_n(bool(reg_f & 0b00000010))
    flag_p = bool(reg_f & 0b00000100)
    fflag_3(bool(reg_f & 0b00001000))
    flag_h = bool(reg_f & 0b00010000)
    fflag_5(bool(reg_f & 0b00100000))
    flag_z = bool(reg_f & 0b01000000)
    flag_s = bool(reg_f & 0b10000000)


def dec2hex16(data):
    # Dec to hex visual converter: 0 -> #0000
    return ('%4s' % str(hex(data))[2:]).replace(' ', '0').upper()


def dec2hex8(data):
    # Dec to hex visual converter: 0 -> #00
    return ('%2s' % str(hex(data))[2:]).replace(' ', '0').upper()


def disp4b(data):
    # Display four bytes in HEX: 00 00 00 00
    return '%s %s %s %s' % (dec2hex8(read_mem(data & 0xffff)), dec2hex8(read_mem((data + 1) & 0xffff)),
                            dec2hex8(read_mem((data + 2) & 0xffff)), dec2hex8(read_mem((data + 3) & 0xffff)))


def display_regs():
    global memory
    # Display all registers
    flags2f()
    print('PC:', dec2hex16(pc), disp4b(pc), '\t', 'SP: ', dec2hex16(sp), disp4b(sp))
    reg_af = reg_a * 256 + reg_f
    reg_af_ = reg_a_ * 256 + reg_f_
    print('AF:', dec2hex16(reg_af), disp4b(reg_af), '\t', 'AF\':', dec2hex16(reg_af_), disp4b(reg_af_))
    reg_bc = reg_b * 256 + reg_c
    reg_bc_ = reg_b_ * 256 + reg_c_
    print('BC:', dec2hex16(reg_bc), disp4b(reg_bc), '\t', 'BC\':', dec2hex16(reg_bc_), disp4b(reg_bc_))
    reg_de = reg_d * 256 + reg_e
    reg_de_ = reg_d_ * 256 + reg_e_
    print('DE:', dec2hex16(reg_de), disp4b(reg_de), '\t', 'DE\':', dec2hex16(reg_de_), disp4b(reg_de_))
    reg_hl = reg_h * 256 + reg_l
    reg_hl_ = reg_h_ * 256 + reg_l_
    print('HL:', dec2hex16(reg_hl), disp4b(reg_hl), '\t', 'HL\':', dec2hex16(reg_hl_), disp4b(reg_hl_))
    reg_ix = reg_ixh * 256 + reg_ixl
    reg_iy = reg_iyh * 256 + reg_iyl
    print('IX:', dec2hex16(reg_ix), disp4b(reg_ix), '\t', 'IY: ', dec2hex16(reg_iy), disp4b(reg_iy))
    print('IR:', dec2hex16(reg_i * 256 + reg_r))
    print('SZ5H3PNC')
    print(('%8s' % str(bin(reg_f))[2:]).replace(' ', '0'))
    print()


def byte_signed(a):
    # From 32int to signed 8byte
    return (a > 127) and (a - 256) or a


def and_a(reg):
    global reg_a, flag_p, flag_h, flag_c, flag_z, flag_s
    if not i8080:
        flag_h = True
    else:
        flag_h = bool((reg_a | reg) & 0x08)
    reg_a &= reg
    flag_s = bool(reg_a & 0b10000000)
    flag_z = not reg_a
    flag_p = p_table[reg_a]
    flag_c = False
    fflag_n(False)
    fflag_3(bool(reg_a & 0b00001000))
    fflag_5(bool(reg_a & 0b00100000))
    return


def xor_a(reg):
    global reg_a, flag_p, flag_h, flag_c, flag_z, flag_s
    reg_a ^= reg
    flag_s = bool(reg_a & 0b10000000)
    flag_z = not reg_a
    flag_h = False
    flag_p = p_table[reg_a]
    flag_c = False
    fflag_n(False)
    fflag_3(bool(reg_a & 0b00001000))
    fflag_5(bool(reg_a & 0b00100000))
    return


def or_a(reg):
    global reg_a, flag_p, flag_h, flag_c, flag_z, flag_s
    reg_a |= reg
    flag_s = bool(reg_a & 0b10000000)
    flag_z = not reg_a
    flag_h = False
    flag_p = p_table[reg_a]
    flag_c = False
    fflag_n(False)
    fflag_3(bool(reg_a & 0b00001000))
    fflag_5(bool(reg_a & 0b00100000))
    return


def cp_a(reg):
    global reg_a, flag_p, flag_h, flag_c, flag_z, flag_s
    reg_temp = reg_a - reg
    index = ((reg_a & 0x88) >> 1) | ((reg & 0x88) >> 2) | ((reg_temp & 0x88) >> 3)
    flag_s = bool(reg_temp & 0b10000000)
    flag_z = not (reg_temp & 0xff)
    flag_h = not sub_h_table[index & 0x7]
    flag_c = bool(reg_temp & 0x100)
    if not i8080:
        flag_p = flag_p != bool(reg_temp & 0b10000000)
    else:
        flag_p = p_table[reg_temp & 0xff]
    fflag_n(True)
    fflag_3(bool(reg & 0b00001000))
    fflag_5(bool(reg & 0b00100000))
    return


def add_a(reg):
    global reg_a, flag_p, flag_h, flag_c, flag_z, flag_s
    reg_temp = reg_a + reg
    index = ((reg_a & 0x88) >> 1) | ((reg & 0x88) >> 2) | ((reg_temp & 0x88) >> 3)
    reg_a = reg_temp & 0xff
    flag_s = bool(reg_a & 0b10000000)
    flag_z = not reg_a
    flag_h = h_table[index & 0x7]
    if not i8080:
        flag_p = flag_p != bool(reg_a & 0b10000000)
    else:
        flag_p = p_table[reg_a]
    flag_c = bool(reg_temp & 0x100)
    fflag_n(False)
    fflag_3(bool(reg_a & 0b00001000))
    fflag_5(bool(reg_a & 0b00100000))
    return


def adc_a(reg):
    global reg_a, flag_p, flag_h, flag_c, flag_z, flag_s
    reg_temp = reg_a + reg + flag_c
    index = ((reg_a & 0x88) >> 1) | ((reg & 0x88) >> 2) | ((reg_temp & 0x88) >> 3)
    reg_a = reg_temp & 0xff
    flag_s = bool(reg_a & 0b10000000)
    flag_z = not reg_a
    flag_h = h_table[index & 0x7]
    if not i8080:
        flag_p = flag_p != bool(reg_a & 0b10000000)
    else:
        flag_p = p_table[reg_a]
    flag_c = bool(reg_temp & 0x100)
    fflag_n(False)
    fflag_3(bool(reg_a & 0b00001000))
    fflag_5(bool(reg_a & 0b00100000))
    return


def sub_a(reg):
    global reg_a, flag_p, flag_h, flag_c, flag_z, flag_s
    reg_temp = reg_a - reg
    index = ((reg_a & 0x88) >> 1) | ((reg & 0x88) >> 2) | ((reg_temp & 0x88) >> 3)
    reg_a = reg_temp & 0xff
    flag_s = bool(reg_a & 0b10000000)
    flag_z = not reg_a
    flag_h = not sub_h_table[index & 0x7]
    if not i8080:
        flag_p = flag_p != bool(reg_a & 0b10000000)
    else:
        flag_p = p_table[reg_a]
    flag_c = bool(reg_temp & 0x100)
    fflag_n(True)
    fflag_3(bool(reg_a & 0b00001000))
    fflag_5(bool(reg_a & 0b00100000))
    return


def sbc_a(reg):
    global reg_a, flag_p, flag_h, flag_c, flag_z, flag_s
    reg_temp = reg_a - reg - flag_c
    index = ((reg_a & 0x88) >> 1) | ((reg & 0x88) >> 2) | ((reg_temp & 0x88) >> 3)
    reg_a = reg_temp & 0xff
    flag_s = bool(reg_a & 0b10000000)
    flag_z = not reg_a
    flag_h = not sub_h_table[index & 0x7]
    if not i8080:
        flag_p = flag_p != bool(reg_a & 0b10000000)
    else:
        flag_p = p_table[reg_a]
    flag_c = bool(reg_temp & 0x100)
    fflag_n(True)
    fflag_3(bool(reg_a & 0b00001000))
    fflag_5(bool(reg_a & 0b00100000))
    return


def byte2mem(addr, byte):
    # Write one byte to memory address
    # ROM write blocking and memory mapping here
    global memory

    # # ZX Spectrum ROM block writing
    # if addr > 0x3fff:
    #     memory[addr] = byte

    # Specialist ROM block writing and VV55A ports
    global vv55a_mode

    if addr < 0xc000:
        memory[addr] = byte

    if 0xf7ff < addr <= 0xffff:
        # # For Ryumik test of Specialist
        # if ((addr & 0b11) == 0) and (byte == 0x82):
        #     ports = ports_82[:]
        #     ports[0] = byte
        #     for i in range(0, 2048, 4):
        #         memory[0xf800 + i:0xf804 + i] = ports[0:4]
        #
        # if ((addr & 0b11) == 2) and (byte == 0x82):
        #     ports = ports_82[:]
        #     ports[2] = byte
        #     for i in range(0, 2048, 4):
        #         memory[0xf800 + i:0xf804 + i] = ports[0:4]
        #
        # if ((addr & 0b11) == 1) and (byte == 0x91):
        #     ports = ports_91[:]
        #     ports[1] = byte
        #     for i in range(0, 2048, 4):
        #         memory[0xf800 + i:0xf804 + i] = ports[0:4]
        #
        # if ((addr & 0b11) == 2) and (byte == 0x91):
        #     ports = ports_91[:]
        #     ports[2] = (ports_91[2] & 0x0f) | (byte & 0xf0)
        #     for i in range(0, 2048, 4):
        #         memory[0xf800 + i:0xf804 + i] = ports[0:4]

        # Main emulation
        if ((addr & 0b11) == 3) and (byte == 0x91):
            vv55a_mode = byte
            for i in range(0, 2048, 4):
                memory[0xf800 + i:0xf804 + i] = ports_91[0:4]

        if ((addr & 0b11) == 3) and (byte == 0x82):
            vv55a_mode = byte
            for i in range(0, 2048, 4):
                memory[0xf800 + i:0xf804 + i] = ports_82[0:4]


def read_mem(addr):
    # Read one byte from memory address
    # Configure memory mapping here
    global memory
    # # Specialist
    # if 0xf7ff < addr <= 0xffff:
    #     pass
    #     # print(dec2hex16(pc), dec2hex8(vv55a_mode), dec2hex16(addr), memory[0xff00:0xff04])
    return memory[addr]


def byte2port(port, byte):
    # Write one byte to XXXX port
    print('Send %s to %s port' % (hex(byte), hex(port)))
    return


def read_port(port):
    # Read one byte from XXXX port
    print('Read %s port' % hex(port))
    return 0


def inc_pc(inc=1):
    # PC increment
    return pc + inc & 0xffff


def inc_reg(reg):
    global flag_p, flag_h, flag_z, flag_s
    flag_p = bool(reg == 0x7f)
    flag_h = reg + 1 & 0x10 != reg & 0x10
    reg = reg + 1 & 0xff
    flag_z = not reg
    flag_s = bool(reg & 0b10000000)
    fflag_n(False)
    fflag_3(bool(reg & 0b00001000))
    fflag_5(bool(reg & 0b00100000))
    return reg


def dec_reg(reg):
    global flag_p, flag_h, flag_z, flag_s
    flag_p = bool(reg == 0x80)
    flag_h = reg - 1 & 0x10 != reg & 0x10
    reg = reg - 1 & 0xff
    flag_z = not reg
    flag_s = bool(reg & 0b10000000)
    fflag_n(True)
    fflag_3(bool(reg & 0b00001000))
    fflag_5(bool(reg & 0b00100000))
    return reg


# CPU instructions set emulation

# 00 XXX XXX opcodes group

def b00000000():  # NOP
    global pc, ticks
    pc = inc_pc()
    ticks += 4
    return


def b00001000():  # EX AF,AF'
    global pc, ticks, reg_a, reg_a_, reg_f, reg_f_
    reg_a, reg_a_ = reg_a_, reg_a
    flags2f()
    reg_f, reg_f_ = reg_f_, reg_f
    f2flags()
    pc = inc_pc()
    ticks += 4
    return


def b00010000():  # DJNZ d
    global pc, ticks, reg_b
    reg_b -= 1
    if reg_b == 0:
        pc = inc_pc(2)
        ticks += 8
        return
    else:
        pc = inc_pc(2) + byte_signed(read_mem(inc_pc())) & 0xffff
        ticks += 13
        return


def b00011000():  # JR d
    global pc, ticks
    pc = inc_pc(2) + byte_signed(read_mem(inc_pc())) & 0xffff
    ticks += 12
    return


def b00100000():  # JR СС,d
    global pc, ticks
    if globals()[conditions[(opcode & 0b010000) >> 4]] == bool(opcode & 0b001000):
        pc = inc_pc(2) + byte_signed(read_mem(inc_pc())) & 0xffff
        ticks += 12
        return
    else:
        pc = inc_pc(2)
        ticks += 7
        return


def b00000001():  # LD RP,nn
    global pc, ticks, reg_b, reg_c, reg_d, reg_e, reg_h, reg_l
    index = (opcode & 0b110000) >> 4
    globals()[reg_pairs[index][1]] = read_mem(inc_pc())
    globals()[reg_pairs[index][0]] = read_mem(inc_pc(2))
    pc = inc_pc(3)
    ticks += 10
    return


def b00110001():  # LD SP,nn
    global pc, ticks, sp
    sp = read_mem(inc_pc(2)) * 256 + read_mem(inc_pc())
    pc = inc_pc(3)
    ticks += 10
    return


def b00001001():  # ADD HL,RP
    global pc, ticks, reg_h, reg_l, flag_c, flag_h
    index = (opcode & 0b110000) >> 4
    reg_l += globals()[reg_pairs[index][1]]
    if not i8080:
        flag_h = reg_h + globals()[reg_pairs[index][0]] + \
                 bool((reg_l + globals()[reg_pairs[index][1]]) & 0x100) & 0x10 != reg_h & 0x10
    reg_h += globals()[reg_pairs[index][0]] + bool(reg_l & 0x100)
    reg_l &= 0xff
    flag_c = bool(reg_h & 0x100)
    reg_h &= 0xff
    fflag_n(False)
    fflag_3(bool(reg_h & 0b00001000))
    fflag_5(bool(reg_h & 0b00100000))
    pc = inc_pc()
    ticks += 11
    return


def b00111001():  # ADD HL,SP
    global pc, ticks, reg_h, reg_l, flag_c, flag_h
    reg_l += sp % 256
    if not i8080:
        flag_h = reg_h + sp // 256 + bool((reg_l + sp % 256) & 0x100) & 0x10 != reg_h & 0x10
    reg_h += sp // 256 + bool(reg_l & 0x100)
    reg_l &= 0xff
    flag_c = bool(reg_h & 0x100)
    reg_h &= 0xff
    fflag_n(False)
    fflag_3(bool(reg_h & 0b00001000))
    fflag_5(bool(reg_h & 0b00100000))
    pc = inc_pc()
    ticks += 11
    return


def b00010010():  # LD (DE),A
    global pc, ticks
    byte2mem(reg_d * 256 + reg_e, reg_a)
    pc = inc_pc()
    ticks += 7
    return


def b00000010():  # LD (BC),A
    global pc, ticks
    byte2mem(reg_b * 256 + reg_c, reg_a)
    pc = inc_pc()
    ticks += 7
    return


def b00011010():  # LD A,(DE)
    global pc, ticks, reg_a
    reg_a = read_mem(reg_d * 256 + reg_e)
    pc = inc_pc()
    ticks += 7
    return


def b00001010():  # LD A,(BC)
    global pc, ticks, reg_a
    reg_a = read_mem(reg_b * 256 + reg_c)
    pc = inc_pc()
    ticks += 7
    return


def b00100010():  # LD (nn),HL
    global pc, ticks
    byte2mem(read_mem(inc_pc(2)) * 256 + read_mem(inc_pc()), reg_l)
    byte2mem(read_mem(inc_pc(2)) * 256 + read_mem(inc_pc()) + 1 & 0xffff, reg_h)
    pc = inc_pc(3)
    ticks += 16
    return


def b00101010():  # LD HL,(nn)
    global pc, ticks, reg_h, reg_l
    reg_l = read_mem(read_mem(inc_pc(2)) * 256 + read_mem(inc_pc()))
    reg_h = read_mem(read_mem(inc_pc(2)) * 256 + read_mem(inc_pc()) + 1 & 0xffff)
    pc = inc_pc(3)
    ticks += 16
    return


def b00110010():  # LD (nn),A
    global pc, ticks
    byte2mem(read_mem(inc_pc(2)) * 256 + read_mem(inc_pc()), reg_a)
    pc = inc_pc(3)
    ticks += 13
    return


def b00111010():  # LD A,(nn)
    global pc, ticks, reg_a
    reg_a = read_mem(read_mem(inc_pc(2)) * 256 + read_mem(inc_pc()))
    pc = inc_pc(3)
    ticks += 13
    return


def b00000011():  # INC RP
    global pc, ticks, reg_b, reg_c, reg_d, reg_e, reg_h, reg_l
    index = (opcode & 0b110000) >> 4
    reg_temp = globals()[reg_pairs[index][0]] * 256 + globals()[reg_pairs[index][1]] + 1 & 0xffff
    globals()[reg_pairs[index][0]] = reg_temp // 256
    globals()[reg_pairs[index][1]] = reg_temp % 256
    pc = inc_pc()
    ticks += 6
    return


def b00110011():  # INC SP
    global pc, ticks, sp
    sp = sp + 1 & 0xffff
    pc = inc_pc()
    ticks += 6
    return


def b00001011():  # DEC RP
    global pc, ticks, reg_b, reg_c, reg_d, reg_e, reg_h, reg_l
    index = (opcode & 0b110000) >> 4
    reg_temp = globals()[reg_pairs[index][0]] * 256 + globals()[reg_pairs[index][1]] - 1 & 0xffff
    globals()[reg_pairs[index][0]] = reg_temp // 256
    globals()[reg_pairs[index][1]] = reg_temp % 256
    pc = inc_pc()
    ticks += 6
    return


def b00111011():  # DEC SP
    global pc, ticks, sp
    sp = sp - 1 & 0xffff
    pc = inc_pc()
    ticks += 6
    return


def b00110100():  # INC (HL)
    global pc, ticks, flag_s, flag_z, flag_h, flag_p
    byte2mem(reg_h * 256 + reg_l, inc_reg(read_mem(reg_h * 256 + reg_l)))
    if i8080:
        reg_temp = read_mem(reg_h * 256 + reg_l)
        flag_s = bool(reg_temp & 0b10000000)
        flag_z = not reg_temp
        flag_h = not (reg_temp & 0x0f)
        flag_p = p_table[reg_temp]
    ticks += 11
    pc = inc_pc()
    return


def b00000100():  # INC SSS
    global pc, ticks, flag_s, flag_z, flag_h, flag_p
    globals()[reg_lst[(opcode & 0b111000) >> 3]] = inc_reg(globals()[reg_lst[(opcode & 0b111000) >> 3]])
    if i8080:
        reg_temp = globals()[reg_lst[(opcode & 0b111000) >> 3]]
        flag_s = bool(reg_temp & 0b10000000)
        flag_z = not reg_temp
        flag_h = not (reg_temp & 0x0f)
        flag_p = p_table[reg_temp]
    ticks += 4
    pc = inc_pc()
    return


def b00110101():  # DEC (HL)
    global pc, ticks, flag_s, flag_z, flag_h, flag_p
    byte2mem(reg_h * 256 + reg_l, dec_reg(read_mem(reg_h * 256 + reg_l)))
    if i8080:
        reg_temp = read_mem(reg_h * 256 + reg_l)
        flag_s = bool(reg_temp & 0b10000000)
        flag_z = not reg_temp
        flag_h = not (reg_temp & 0x0f == 0x0f)
        flag_p = p_table[reg_temp]
    ticks += 11
    pc = inc_pc()
    return


def b00000101():  # DEC SSS
    global pc, ticks, flag_s, flag_z, flag_h, flag_p
    globals()[reg_lst[(opcode & 0b111000) >> 3]] = dec_reg(globals()[reg_lst[(opcode & 0b111000) >> 3]])
    if i8080:
        reg_temp = globals()[reg_lst[(opcode & 0b111000) >> 3]]
        flag_s = bool(reg_temp & 0b10000000)
        flag_z = not reg_temp
        flag_h = not (reg_temp & 0x0f == 0x0f)
        flag_p = p_table[reg_temp]
    ticks += 4
    pc = inc_pc()
    return


def b00110110():  # LD (HL),d
    global pc, ticks
    byte2mem(reg_h * 256 + reg_l, read_mem(inc_pc()))
    ticks += 10
    pc = inc_pc(2)
    return


def b00000110():  # LD DDD,d
    global pc, ticks
    globals()[reg_lst[(opcode & 0b111000) >> 3]] = read_mem(inc_pc())
    ticks += 7
    pc = inc_pc(2)
    return


def b00000111():  # RLCA
    global pc, ticks, reg_a, flag_c, flag_h
    reg_a = reg_a << 1
    flag_c = bool(reg_a & 0x100)
    reg_a = (reg_a | flag_c) & 0xff
    if not i8080:
        flag_h = False
    fflag_n(False)
    fflag_3(bool(reg_a & 0b00001000))
    fflag_5(bool(reg_a & 0b00100000))
    pc = inc_pc()
    ticks += 4
    return


def b00001111():  # RRCA
    global pc, ticks, reg_a, flag_c, flag_h
    flag_temp = bool(reg_a & 1)
    reg_a = reg_a >> 1 | (reg_a & 1) << 7
    flag_c = flag_temp
    if not i8080:
        flag_h = False
    fflag_n(False)
    fflag_3(bool(reg_a & 0b00001000))
    fflag_5(bool(reg_a & 0b00100000))
    pc = inc_pc()
    ticks += 4
    return


def b00010111():  # RLA
    global pc, ticks, reg_a, flag_c, flag_h
    reg_a = reg_a << 1 | flag_c
    flag_c = bool(reg_a & 0x100)
    reg_a = reg_a & 0xff
    if not i8080:
        flag_h = False
    fflag_n(False)
    fflag_3(bool(reg_a & 0b00001000))
    fflag_5(bool(reg_a & 0b00100000))
    pc = inc_pc()
    ticks += 4
    return


def b00011111():  # RRA
    global pc, ticks, reg_a, flag_c, flag_h
    flag_temp = bool(reg_a & 1)
    reg_a = reg_a >> 1 | flag_c << 7
    flag_c = flag_temp
    if not i8080:
        flag_h = False
    fflag_n(False)
    fflag_3(bool(reg_a & 0b00001000))
    fflag_5(bool(reg_a & 0b00100000))
    pc = inc_pc()
    ticks += 4
    return


def b00100111():  # DAA
    global pc, ticks, flag_c, reg_a, flag_z, flag_s, flag_p, flag_h
    carry = flag_c
    addition = 0
    if flag_h or ((reg_a & 0x0f) > 0x09):
        addition = 0x06
    if flag_c or (reg_a > 0x9f) or ((reg_a > 0x8f) and ((reg_a & 0x0f) > 0x09)):
        addition |= 0x60
    if reg_a > 0x99:
        carry = True
    add_a(addition)
    flag_c = carry
    pc = inc_pc()
    ticks += 4
    return


def b00101111():  # CPL
    global pc, ticks, reg_a, flag_h
    reg_a ^= 0xff
    if not i8080:
        flag_h = True
    fflag_n(True)
    fflag_3(bool(reg_a & 0b00001000))
    fflag_5(bool(reg_a & 0b00100000))
    pc = inc_pc()
    ticks += 4
    return


def b00110111():  # SCF
    global pc, ticks, flag_c, flag_h
    flag_c = True
    if not i8080:
        flag_h = False
    fflag_n(False)
    fflag_3(bool(reg_a & 0b00001000))
    fflag_5(bool(reg_a & 0b00100000))
    pc = inc_pc()
    ticks += 4
    return


def b00111111():  # CCF
    global pc, ticks, flag_c, flag_h
    if not i8080:
        flag_h = flag_c
    flag_c = not flag_c
    fflag_n(False)
    fflag_3(bool(reg_a & 0b00001000))
    fflag_5(bool(reg_a & 0b00100000))
    pc = inc_pc()
    ticks += 4
    return


# 01 XXX XXX group

def b01110110():  # HALT
    global ticks
    ticks += 4
    return


def b01000110():  # LD DDD,(HL)
    global pc, ticks
    globals()[reg_lst[(opcode & 0b111000) >> 3]] = read_mem(reg_h * 256 + reg_l)
    pc = inc_pc()
    ticks += 7
    return


def b01110000():  # LD (HL),SSS
    global pc, ticks
    byte2mem(reg_h * 256 + reg_l, globals()[reg_lst[opcode & 0b111]])
    pc = inc_pc()
    ticks += 7
    return


def b01000000():  # LD DDD,SSS
    global pc, ticks
    globals()[reg_lst[(opcode & 0b111000) >> 3]] = globals()[reg_lst[opcode & 0b111]]
    pc = inc_pc()
    ticks += 4
    return


# 10 XXX XXX group

def b10000110():  # ADD A,(HL)
    global pc, ticks
    add_a(read_mem(reg_h * 256 + reg_l))
    pc = inc_pc()
    ticks += 7
    return


def b10000000():  # ADD A,SSS
    global pc, ticks
    add_a(globals()[reg_lst[opcode & 0b111]])
    pc = inc_pc()
    ticks += 4
    return


def b10001110():  # ADC A,(HL)
    global pc, ticks
    adc_a(read_mem(reg_h * 256 + reg_l))
    pc = inc_pc()
    ticks += 7
    return


def b10001000():  # ADC A,SSS
    global pc, ticks
    adc_a(globals()[reg_lst[opcode & 0b111]])
    pc = inc_pc()
    ticks += 4
    return


def b10010110():  # SUB A,(HL)
    global pc, ticks
    sub_a(read_mem(reg_h * 256 + reg_l))
    pc = inc_pc()
    ticks += 7
    return


def b10010000():  # SUB A,SSS
    global pc, ticks
    sub_a(globals()[reg_lst[opcode & 0b111]])
    pc = inc_pc()
    ticks += 4
    return


def b10011110():  # SBC A,(HL)
    global pc, ticks
    sbc_a(read_mem(reg_h * 256 + reg_l))
    pc = inc_pc()
    ticks += 7
    return


def b10011000():  # SBC A,SSS
    global pc, ticks
    sbc_a(globals()[reg_lst[opcode & 0b111]])
    pc = inc_pc()
    ticks += 4
    return


def b10100110():  # AND A,(HL)
    global pc, ticks
    and_a(read_mem(reg_h * 256 + reg_l))
    pc = inc_pc()
    ticks += 7
    return


def b10100000():  # AND A,SSS
    global pc, ticks
    and_a(globals()[reg_lst[opcode & 0b111]])
    pc = inc_pc()
    ticks += 4
    return


def b10101110():  # XOR A,(HL)
    global pc, ticks
    xor_a(read_mem(reg_h * 256 + reg_l))
    pc = inc_pc()
    ticks += 7
    return


def b10101000():  # XOR A,SSS
    global pc, ticks
    xor_a(globals()[reg_lst[opcode & 0b111]])
    pc = inc_pc()
    ticks += 4
    return


def b10110110():  # OR A,(HL)
    global pc, ticks
    or_a(read_mem(reg_h * 256 + reg_l))
    pc = inc_pc()
    ticks += 7
    return


def b10110000():  # OR A,SSS
    global pc, ticks
    or_a(globals()[reg_lst[opcode & 0b111]])
    pc = inc_pc()
    ticks += 4
    return


def b10111110():  # CP (HL)
    global pc, ticks
    cp_a(read_mem(reg_h * 256 + reg_l))
    pc = inc_pc()
    ticks += 7
    return


def b10111000():  # CP SSS
    global pc, ticks
    cp_a(globals()[reg_lst[opcode & 0b111]])
    pc = inc_pc()
    ticks += 4
    return


# 11 XXX XXX group

def b11000000():  # RET CCC
    global pc, ticks, sp
    if globals()[conditions[(opcode & 0b110000) >> 4]] == bool(opcode & 0b001000):
        pc = read_mem(sp) + read_mem(sp + 1 & 0xffff) * 256
        sp = sp + 2 & 0xffff
        ticks += 11
        return
    else:
        ticks += 5
        pc = inc_pc()
        return


def b11000001():  # POP RP
    global pc, ticks, reg_c, reg_b, reg_e, reg_d, reg_l, reg_h, sp
    globals()[reg_pairs[(opcode & 0b110000) >> 4][0]] = read_mem(sp + 1 & 0xffff)
    globals()[reg_pairs[(opcode & 0b110000) >> 4][1]] = read_mem(sp)
    sp = sp + 2 & 0xffff
    ticks += 10
    pc = inc_pc()
    return


def b11110001():  # POP AF
    global pc, ticks, reg_f, reg_a, sp
    reg_f = read_mem(sp)
    if i8080:
        reg_f &= 0b11010101
        reg_f |= 0b00000010
    f2flags()
    reg_a = read_mem(sp + 1 & 0xffff)
    sp = sp + 2 & 0xffff
    ticks += 10
    pc = inc_pc()
    return


def b11001001():  # RET
    global pc, ticks, sp
    pc = read_mem(sp) + read_mem(sp + 1 & 0xffff) * 256
    sp = sp + 2 & 0xffff
    ticks += 10
    return


def b11011001():  # EXX
    global pc, ticks, reg_b, reg_b_, reg_c, reg_c_, reg_d, reg_d_, reg_e, reg_e_, reg_h, reg_h_, reg_l, reg_l_
    reg_b, reg_b_ = reg_b_, reg_b
    reg_c, reg_c_ = reg_c_, reg_c
    reg_d, reg_d_ = reg_d_, reg_d
    reg_e, reg_e_ = reg_e_, reg_e
    reg_h, reg_h_ = reg_h_, reg_h
    reg_l, reg_l_ = reg_l_, reg_l
    pc = inc_pc()
    ticks += 4
    return


def b11101001():  # JP (HL)
    global pc, ticks
    pc = reg_h * 256 + reg_l
    ticks += 4
    return


def b11111001():  # LD SP,HL
    global pc, ticks, sp
    sp = reg_h * 256 + reg_l
    pc = inc_pc()
    ticks += 6
    return


def b11000010():  # JP CCC,nn
    global pc, ticks
    if globals()[conditions[(opcode & 0b110000) >> 4]] == bool(opcode & 0b001000):
        pc = read_mem(inc_pc()) + read_mem(inc_pc(2)) * 256
        ticks += 10
        return
    else:
        ticks += 10
        pc = inc_pc(3)
        return


def b11000011():  # JP nn
    global pc, ticks
    pc = read_mem(inc_pc()) + read_mem(inc_pc(2)) * 256
    ticks += 6
    return


def b11001011():
    # Prefixes #CB, #DD, #ED, #FD
    global pc
    pc = inc_pc()
    return


def b11010011():  # OUT (d),A
    global pc, ticks
    byte2port(reg_a * 256 + read_mem(inc_pc()), reg_a)
    pc = inc_pc(2)
    ticks += 11
    return


def b11011011():
    global pc, ticks, reg_a
    reg_a = read_port(reg_a * 256 + read_mem(inc_pc()))
    pc = inc_pc(2)
    ticks += 11
    return


def b11100011():  # EX (SP),HL
    global pc, ticks, reg_l, reg_h
    reg_templ = read_mem(sp)
    reg_temph = read_mem(sp + 1 & 0xffff)
    byte2mem(sp, reg_l)
    byte2mem(sp + 1 & 0xffff, reg_h)
    reg_l = reg_templ
    reg_h = reg_temph
    pc = inc_pc()
    ticks += 19
    return


def b11101011():  # EX DE,HL
    global pc, ticks, reg_d, reg_h, reg_e, reg_l
    reg_d, reg_h = reg_h, reg_d
    reg_e, reg_l = reg_l, reg_e
    pc = inc_pc()
    ticks += 4
    return


def b11110011():  # DI
    global pc, ticks, iff1, iff2
    iff1 = False
    iff2 = False
    pc = inc_pc()
    ticks += 4
    return


def b11111011():  # EI
    global pc, ticks, iff1, iff2
    iff1 = True
    iff2 = True
    pc = inc_pc()
    ticks += 4
    return


def b11000100():  # CALL CCC,nn
    global pc, ticks, sp
    reg_temp = inc_pc(3)
    if globals()[conditions[(opcode & 0b110000) >> 4]] == bool(opcode & 0b001000):
        sp = sp - 2 & 0xffff
        byte2mem(sp, reg_temp % 256)
        byte2mem(sp + 1 & 0xffff, reg_temp // 256)
        pc = read_mem(inc_pc()) + read_mem(inc_pc(2)) * 256
        ticks += 17
        return
    else:
        ticks += 10
        pc = reg_temp
        return


def b11000101():  # PUSH RP
    global pc, ticks, sp
    sp = sp - 2 & 0xffff
    byte2mem(sp, globals()[reg_pairs[(opcode & 0b110000) >> 4][1]])
    byte2mem(sp + 1 & 0xffff, globals()[reg_pairs[(opcode & 0b110000) >> 4][0]])
    pc = inc_pc()
    ticks += 11
    return


def b11110101():  # PUSH AF
    global pc, ticks, sp
    sp = sp - 2 & 0xffff
    flags2f()
    byte2mem(sp, reg_f)
    byte2mem(sp + 1 & 0xffff, reg_a)
    pc = inc_pc()
    ticks += 11
    return


def b11001101():  # CALL nn
    global pc, ticks, sp
    sp = sp - 2 & 0xffff
    reg_temp = inc_pc(3)
    byte2mem(sp, reg_temp % 256)
    byte2mem(sp + 1 & 0xffff, reg_temp // 256)
    pc = read_mem(inc_pc()) + read_mem(inc_pc(2)) * 256
    ticks += 17
    return


def b11000110():  # ADD A,d
    global pc, ticks
    add_a(read_mem(inc_pc()))
    pc = inc_pc(2)
    ticks += 7
    return


def b11001110():  # ADC A,d
    global pc, ticks
    adc_a(read_mem(inc_pc()))
    pc = inc_pc(2)
    ticks += 7
    return


def b11010110():  # SUB A,d
    global pc, ticks
    sub_a(read_mem(inc_pc()))
    pc = inc_pc(2)
    ticks += 7
    return


def b11011110():  # SBC A,d
    global pc, ticks
    sbc_a(read_mem(inc_pc()))
    pc = inc_pc(2)
    ticks += 7
    return


def b11100110():  # AND A,d
    global pc, ticks
    and_a(read_mem(inc_pc()))
    pc = inc_pc(2)
    ticks += 7
    return


def b11101110():  # XOR A,d
    global pc, ticks
    xor_a(read_mem(inc_pc()))
    pc = inc_pc(2)
    ticks += 7
    return


def b11110110():  # OR A,d
    global pc, ticks
    or_a(read_mem(inc_pc()))
    pc = inc_pc(2)
    ticks += 7
    return


def b11111110():  # CP A,d
    global pc, ticks
    cp_a(read_mem(inc_pc()))
    pc = inc_pc(2)
    ticks += 7
    return


def b11000111():  # RST NNN
    global pc, ticks, sp
    sp = sp - 2 & 0xffff
    reg_temp = inc_pc()
    byte2mem(sp, reg_temp % 256)
    byte2mem(sp + 1 & 0xffff, reg_temp // 256)
    pc = ((opcode & 0b00111000) >> 3) * 8
    ticks += 11
    return


opcodes_z80 = {0x00: b00000000, 0x08: b00001000, 0x10: b00010000, 0x18: b00011000,
               0x20: b00100000, 0x28: b00100000, 0x30: b00100000, 0x38: b00100000,
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
               0xC9: b11001001, 0xD9: b11011001, 0xE9: b11101001, 0xF9: b11111001,
               0xC2: b11000010, 0xCA: b11000010, 0xD2: b11000010, 0xDA: b11000010,
               0xE2: b11000010, 0xEA: b11000010, 0xF2: b11000010, 0xFA: b11000010,
               0xC3: b11000011, 0xCB: b11001011, 0xD3: b11010011, 0xDB: b11011011,
               0xE3: b11100011, 0xEB: b11101011, 0xF3: b11110011, 0xFB: b11111011,
               0xC4: b11000100, 0xCC: b11000100, 0xD4: b11000100, 0xDC: b11000100,
               0xE4: b11000100, 0xEC: b11000100, 0xF4: b11000100, 0xFC: b11000100,
               0xC5: b11000101, 0xD5: b11000101, 0xE5: b11000101, 0xF5: b11110101,
               0xCD: b11001101, 0xDD: b11001011, 0xED: b11001011, 0xFD: b11001011,
               0xC6: b11000110, 0xCE: b11001110, 0xD6: b11010110, 0xDE: b11011110,
               0xE6: b11100110, 0xEE: b11101110, 0xF6: b11110110, 0xFE: b11111110,
               0xC7: b11000111, 0xCF: b11000111, 0xD7: b11000111, 0xDF: b11000111,
               0xE7: b11000111, 0xEF: b11000111, 0xF7: b11000111, 0xFF: b11000111,
               }

opcodes_i8080 = {0x00: b00000000, 0x08: b00000000, 0x10: b00000000, 0x18: b00000000,
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
                 0xE7: b11000111, 0xEF: b11000111, 0xF7: b11000111, 0xFF: b11000111,
                 }

if i8080:
    opcodes = opcodes_i8080
else:
    opcodes = opcodes_z80


def core():
    global opcode
    opcode = memory[pc]
    return opcodes[opcode]()


def fill_memory(codes):
    # Fill memory by codes
    print(codes)
    i = 0
    for code in codes:
        memory[pc + i & 0xffff] = code
        i += 1


if __name__ == '__main__':
    # For debugging CPU emulation
    pc = 0x8000
    sp = 0x8ede

    flag_c = True
    # flag_n = True
    # flag_v = True
    # flag_3 = True
    # flag_h = True
    # flag_5 = True
    # flag_z = True
    # flag_s = True

    reg_a = 0x08
    reg_b = 0x1d
    reg_c = 0x00
    reg_d = 0x80
    reg_e = 0x00
    reg_h = 0xff
    reg_l = 0x00

    fill_memory([0xe1, 0x01, 0x1d])

    display_regs()
    core()
    display_regs()
