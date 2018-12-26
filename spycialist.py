#!/usr/bin/env python
# -*- coding: utf-8 -*-

# sPycialist - Specialist PC Emulator
# (C) Stanislav Yudin (CityAceE)
# http://zx-pk.ru
#
# ver.0.1 December 2018

import pygame

import z80
import spyc_screen
import spyc_loader
import spyc_keyboard


GAME = 'zoo.rks'
ROM = 'system.rom'

INT_TICKS = 69888  # Ticks number between two interrupts

z80.pc = spyc_loader.game(GAME)
spyc_loader.rom(ROM, 0xc000)
z80.pc = 0xc000

debug = False
running = True
try:
    while running:

        # START OF MAIN LOOP

        # # FOR DEBUGGING
        # if (z80.pc == 0x1973) and (z80.reg_h == 0x3d) and (z80.reg_l == 0xf8):  # Trap conditions
        #     debug = True
        #     print('PC:', hex(z80.pc))
        #     pass
        # if debug:
        #     spyc_screen.update()
        #     z80.display_regs()  # Set breakpoint here

        z80.core()
        if z80.ticks > INT_TICKS:
            z80.ticks = 0
            spyc_screen.update()
        # END OF MAIN LOOP

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                spyc_keyboard.keydown(event.key)
            if event.type == pygame.KEYUP:
                spyc_keyboard.keyup(event.key)

    pygame.quit()
except SystemExit:
    pygame.quit()
