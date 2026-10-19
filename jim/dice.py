#!/usr/bin/env python2.7 -t
###############################################################################
#
# File:         dice.py
# RCS:          $Header: $
# Description:  Dice Simulator
# Author:       Jim Randell
# Created:      Sun Sep 25 09:11:13 2011
# Modified:     Mon Sep 26 16:09:39 2011 (Jim Randell) jim.randell@gmail.com
# Language:     Python
# Package:      N/A
# Status:       Experimental (Do Not Distribute)
#
# (C) Copyright 2011, Jim Randell, all rights reserved.
#
###############################################################################
# -*- mode: Python; py-indent-offset: 2; -*-

__author__ = "Jim Randell <jim.randell@gmail.com>"
__version__ = "2011-09-26"



DEFAULTS = {
  # colours: background, foreground, highlight
  'bg': 'black', 'fg': 'white', 'hl': 'red',
  # fonts
  'font': 'Arial', 'font-size': 72,
  #'unicode': False, 'dice-font': 'Arial', 'dice-font-size': 720,
  'unicode': True, 'dice-font': 'Apple Symbols', 'dice-font-size': 760, # around 760 for two dice, 600 for three
  # number and type of dice
  'dice': [6] * 2, # two six-sided dice
  # roll sound
  'sound': '/System/Library/Sounds/Pop.aiff',
  # game type
  'game': 'floundering',
  # debug
  'debug': True,
}



import pygame
pygame.Colour = pygame.Color # British English, please

import random

import argparse



class App:


  def __init__(self):

    args = self.args()
    self.debug = args.debug
    self.bg = pygame.Colour(args.bg)
    self.fg = pygame.Colour(args.fg)
    self.red = pygame.Colour(args.hl)
    self.flags = pygame.FULLSCREEN
    self.pointer = False
    self.font = [ args.font, args.font_size ]
    self.unicode = args.unicode
    self.dice_font = [ args.dice_font, args.dice_font_size ]
    self.dice_n = args.dice
    self.sound = args.sound
    self.specials = []
    if args.game == 'floundering':
      # special throws for "The Merry Game of Floundering"
      self.specials.append((lambda d: len(set(d)) == 1, 'Double!'))
      self.specials.append((lambda d: set(d) == set((1, 6)), '6 and 1'))

    self.dice = self.dice_n[:]
    self.rolls = 0



  def args(self):
    arg = argparse.ArgumentParser(description='Dice Emulator.')
    arg.add_argument('-fg', '--foreground', dest='fg', default=DEFAULTS['fg'], help='foreground colour (default: {d})'.format(d=DEFAULTS['fg']))
    arg.add_argument('-bg', '--background', dest='bg', default=DEFAULTS['bg'], help='background colour (default: {d})'.format(d=DEFAULTS['bg']))
    arg.add_argument('-hl', '--highlight', dest='hl', default=DEFAULTS['hl'], help='highlight colour (default: {d})'.format(d=DEFAULTS['hl']))
    arg.add_argument('-fn', '--font', dest='font', default=DEFAULTS['font'], help='font (default: {d})'.format(d=DEFAULTS['font']))
    arg.add_argument('-fs', '--font-size', dest='font_size', type=int, default=DEFAULTS['font-size'], help='font size (default: {d}'.format(d=DEFAULTS['font-size']))
    arg.add_argument('-u', '--unicode', dest='unicode', action='store_true', default=True, help='enable Unicode dice characters (default: enabled)')
    arg.add_argument('-a', '--ascii', dest='unicode', action='store_false', help='enable numeric dice characters (default: disabled)')
    arg.add_argument('-dfn', '--dice-font', dest='dice_font', default=DEFAULTS['dice-font'], help='dice font (default: {d})'.format(d=DEFAULTS['dice-font']))
    arg.add_argument('-dfs', '--dice-font-size', dest='dice_font_size', type=int, default=DEFAULTS['dice-font-size'], help='dice font size (default: {d})'.format(d=DEFAULTS['dice-font-size']))
    arg.add_argument('-s', '--sound', dest='sound', default=DEFAULTS['sound'], help='roll sound (default: {d})'.format(d=DEFAULTS['sound']))
    arg.add_argument('-g', '--game', dest='game', choices=('floundering', 'none'), default=DEFAULTS['game'], help='dice game (default: {d})'.format(d=DEFAULTS['game']))
    arg.add_argument('-d', '--debug', dest='debug', action='store_true', help='enable debug (default: disabled)')
    arg.add_argument(metavar='N', dest='dice', nargs='*', type=int, default=DEFAULTS['dice'], help='dice number and sides (default: {d})'.format(d=DEFAULTS['dice']))
    return arg.parse_args()



  def init(self):

    pygame.init()
    pygame.display.set_caption('Dice')
    info = pygame.display.Info()
    self.width = info.current_w
    self.height = info.current_h

    if self.debug:
      self.width /= 2
      self.height /= 2
      self.flags = 0
      self.pointer = True
      self.font[1] /= 2
      self.dice_font[1] /= 2
    
    self.screen = pygame.display.set_mode((self.width, self.height), self.flags)
    pygame.mouse.set_visible(self.pointer)

    self.font = pygame.font.SysFont(*self.font, bold=True)
    self.dice_font = pygame.font.SysFont(*self.dice_font, bold=False)

    pygame.mixer.init()
    self.beep = pygame.mixer.Sound(self.sound)

    self.draw()



  def roll(self):
    self.dice = [random.randint(1, n) for n in self.dice_n]
    self.rolls += 1
    self.draw()
    self.beep.play()



  def draw(self):

    # blank the screen
    self.screen.fill(self.bg)

    w = self.width
    h = self.height

    # draw the title
    text = self.font.render('Dice {n}'.format(n=self.rolls), 1, self.fg)
    self.screen.blit(text, [(w - text.get_width())/ 2, 0])
    h1 = text.get_height()

    # draw the dice
    if self.unicode:
      # (9856 is Unicode 1-spot die character)
      dice = ''.join(map(lambda x: unichr(9855 + x), self.dice))
    else:
      # simple ASCII rendering
      dice = ' '.join(map(str, self.dice))

    text = self.dice_font.render(dice, 1, self.fg)
    self.screen.blit(text, [(w - text.get_width()) / 2, h1 + (h - 2*h1 - text.get_height()) / 2])

    # check for specials
    specials = (s[1] for s in self.specials if s[0](self.dice))
    if specials:
      text = self.font.render(' / '.join(specials), 1, self.red)
      self.screen.blit(text, [(w - text.get_width())/ 2, h - 2*h1])

    # draw the total
    total = 'Total = ' + str(sum(self.dice))
    text = self.font.render(total, 1, self.fg)
    self.screen.blit(text, [(w - text.get_width())/ 2, h - h1])

    pygame.display.flip()



  def run(self):

    while True:
      for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
          if event.key in (pygame.K_SPACE, pygame.K_RETURN):
            # space, return
            self.roll()
          elif event.key in (pygame.K_ESCAPE, pygame.K_q):
            # ESC, Q = quit
            return
        elif event.type == pygame.MOUSEBUTTONDOWN:
          # mouse press
          self.roll()
        elif event.type == pygame.QUIT:
          # window quit
          return

          

def main():
  app = App()
  app.init()
  app.run()

main()
