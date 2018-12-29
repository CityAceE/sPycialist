#!/usr/bin/env python
# -*- coding: utf-8 -*-

# sPycialist - Specialist PC Emulator
# (C) Stanislav Yudin (CityAceE)
# http://zx-pk.ru
#
# ver.0.2 December 2018

import pygame

import i8080 as cpu
import spyc_screen
import spyc_loader
import spyc_keyboard


GAME = 'zoo.rks'

ROM = 'system.rom'

INT_TICKS = 69888  # Ticks number between two interrupts

cpu.pc = spyc_loader.game(GAME)
spyc_loader.rom(ROM, 0xc000)
cpu.pc = 0xc000

cpu.sp = 0x7FFF

debug = False
running = True
try:
    while running:

        # START OF MAIN LOOP

        # # FOR DEBUGGING
        # if (cpu.pc == 0xc1ff):  # and (cpu.reg_h == 0x3d) and (cpu.reg_l == 0xf8):  # Trap conditions
        #     debug = True
        #     # print('PC:', hex(cpu.pc))
        #     pass
        # if debug:
        #     # spyc_screen.update()
        #     cpu.display_regs()  # Set breakpoint here

        cpu.core()
        if cpu.ticks > INT_TICKS:
            cpu.ticks = 0
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
