#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Screen emulator (part of sPycialist - Specialist PC Emulator)
# (C) Stanislav Yudin (CityAceE)
# http://zx-pk.ru

import pygame
import i8080 as cpu

SCREEN_WIDTH = 384
SCREEN_HEIGHT = 256
VIDEO_RAM = 0x9000

table_byte = []
for pix in range(256):
    pix_group = [0, 0, 0, 0, 0, 0, 0, 0]
    if pix & 0b00000001:
        pix_group[7] = 255
    if pix & 0b00000010:
        pix_group[6] = 255
    if pix & 0b00000100:
        pix_group[5] = 255
    if pix & 0b00001000:
        pix_group[4] = 255
    if pix & 0b00010000:
        pix_group[3] = 255
    if pix & 0b00100000:
        pix_group[2] = 255
    if pix & 0b01000000:
        pix_group[1] = 255
    if pix & 0b10000000:
        pix_group[0] = 255
    table_byte.append(pix_group)

global screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), 0, 8)
pygame.display.set_caption("sPycialist")
pygame.display.flip()


def update():
    byte_number = 0
    for coord_x in range(0, 384, 8):
        for coord_y in range(256):
            for i in range(8):
                screen.set_at((coord_x + i, coord_y), table_byte[cpu.memory[VIDEO_RAM + byte_number]][i])
            byte_number += 1
    pygame.display.flip()
