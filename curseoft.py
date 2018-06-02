#!/usr/bin/env python2
import sys
import pygame
import main
from game import Game
import worldmap
import versus

if __name__ == "__main__":
	pygame.init()

	# Initialze pygame and set base
	SCREEN = WINDOW_WIDTH, WINDOW_HEIGHT = 780, 640
	window = pygame.display.set_mode(SCREEN)

	game = Game(window)

	# Game start
	game.start_screen()
	while True:
		gameplay = game.new_or_load()

		if gameplay == "game":
			game.set_game()
			worldmap.KINGDOMS[game.loaded_kingdom](game, game.window)
		elif gameplay == "versus":
			versus_game = versus.Versus(game)

	pygame.quit()
	sys.exit(0)