#!/usr/bin/env python
# -*- coding: utf-8 -*-

# File loader (part of sPycialist - Specialist PC Emulator)
# (C) Stanislav Yudin (CityAceE)
# http://zx-pk.ru

import i8080 as cpu


def rom(filename, addr):
    # ROM file loading
    with open(filename, 'rb') as f:
        romfile = f.read()
    cpu.memory[addr: addr + len(romfile)] = romfile[:]


def game(filename):
    # ROM file loading
    with open(filename, 'rb') as f:
        romfile = f.read()
        start = romfile[1] * 256 + romfile[0]
        print('START:', cpu.dec2hex16(start))
        end = romfile[3] * 256 + romfile[2]
        print('END:', cpu.dec2hex16(end))
    cpu.memory[start:end + 2] = romfile[4:4 + end + 2 - start]
    return start
