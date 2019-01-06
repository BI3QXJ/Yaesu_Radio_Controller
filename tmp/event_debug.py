#!/usr/bin/env python
# -*- coding:utf-8 -*-

import pygame
from pygame.locals import *
from sys import exit

pygame.init()
SCREEN_SIZE = (640, 480)
screen = pygame.display.set_mode(SCREEN_SIZE, FULLSCREEN, 32)

font = pygame.font.SysFont("FreeMono", 11)
font_height = font.get_linesize()
event_text = []

while True:
    event = pygame.event.wait()
    event_text.append(str(event))
    # 保证event_text里面只保留一个屏幕的文字
    event_text = event_text[-SCREEN_SIZE[1]//font_height:]

    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            exit()
        elif event.type == KEYDOWN and event.key == K_ESCAPE:
            pygame.quit()
            exit()

    screen.fill((255, 255, 255))

    # 寻找一个合适的起笔位置，最下面开始，留一行的空
    y = SCREEN_SIZE[1] - font_height
    for text in reversed(event_text):
        screen.blit(font.render(text, True, (0, 0, 0)), (0, y))
        y -= font_height
    pygame.display.update()
