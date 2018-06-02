#!/usr/bin/env python2
import sys
from random import choice
import pygame
from kingdoms import Kingdom
from worldmap import worldmap, add_kingdoms, KINGDOMS

def enter_kingdom(leave_current_kingdom, kingdom_name):
	print kingdom_name
	if leave_current_kingdom:
		# Run the function of that kingdom
		return KINGDOMS[kingdom_name]

def home(game, window):
	home = Kingdom(game, window, "Tenebrae")
	game.player.set_kingdom_in(home.name)
	home.load_kingdom("maps/cursed.tmx", "maps/tenebrae.png", "maps/cursednpcs.txt")
	# Game needed things loaded
	game.loaded = True

	try:
		leave_current_kingdom, kingdom_name = home.kingdom_life()
	except TypeError:
		return True
	finally:
		home.clear()
	return enter_kingdom(leave_current_kingdom, kingdom_name)(game, window)

def uwile(game, window):
	uwile_kingdom = Kingdom(game, window, "Uwile_Castle")
	game.player.set_kingdom_in(uwile_kingdom.name)

	uwile_kingdom.load_kingdom("maps/uwile.tmx", "maps/uwile_castle.png", "maps/cursednpcs.txt")

	# Game needed things loaded
	game.loaded = True

	try:
		leave_current_kingdom, kingdom_name = uwile_kingdom.kingdom_life()
	except TypeError:
		return True
	finally:
		uwile_kingdom.clear()
	return enter_kingdom(leave_current_kingdom, kingdom_name)(game, window)


# Add kingdoms to worldmap
add_kingdoms(Tenebrae=home)
add_kingdoms(Uwile_Castle=uwile)

if __name__ == "__main__":
	pass