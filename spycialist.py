#!/usr/bin/env python
# -*- coding: utf-8 -*-

# sPycialist - Specialist PC Emulator
# (C) Stanislav Yudin (CityAceE)
# http://zx-pk.ru
#
# ver.0.4, 2nd December 2019

import pygame
import pygame.surfarray
import numpy as np

import i8080 as cpu
import spyc_loader
import spyc_keyboard

GAME = 'zoo.rks'
ROM = 'system.rom'
CPU_CLOCK = 2  # In MHz. Default Intel 8080 frequency is 2 MHz

cpu.pc = spyc_loader.game(GAME)
spyc_loader.rom(ROM, 0xc000)
cpu.pc = 0xc000
cpu.sp = 0x7FFF
debug = False
running = True
int_ticks = int(CPU_CLOCK * 1000000 / 50)
screen = pygame.display.set_mode((384, 256), 0, 8)
pygame.display.set_caption("sPycialist")


def blitsurface():
    mem = np.reshape(cpu.memory[0x9000:0xc000], (256, 48), 'F')
    bits = np.unpackbits(mem) * 255
    pygame.surfarray.blit_array(screen, np.reshape(bits, (256, 384)).T)


try:
    clock = pygame.time.Clock()
    while running:

        # START OF MAIN LOOP

        # # FOR DEBUGGING
        # if (cpu.pc == 0xc1ff):  # and (cpu.reg_h == 0x3d) and (cpu.reg_l == 0xf8):  # Trap conditions
        #     debug = True
        #     # print('PC:', hex(cpu.pc))
        #     pass
        # if debug:
        #     # blitsurface()
        #     # pygame.display.flip()
        #     cpu.display_regs()  # Set breakpoint here

        cpu.core()
        if cpu.ticks > int_ticks:
            cpu.ticks = 0
            blitsurface()
            pygame.display.flip()
            clock.tick(50)
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
