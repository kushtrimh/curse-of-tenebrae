import pygame
from pytmx.util_pygame import load_pygame
from sprites import *
import solgame
from colors import *

KINGDOMS= {
    # Name  # X   # Y
	"Tenebrae": None,
	"Uwile_Castle": None,
}

def add_kingdoms(**kwargs):
	for kingdom in kwargs:
		KINGDOMS[kingdom] = kwargs[kingdom]

def worldmap(game):
	# Display loading screen until data is loaded
	with game.load():

		# Load map
		tmx_data = load_pygame("maps/map.tmx")

		# Map sprites
		worldmap = Map(game.window, "maps/map.png", 150, 150)
		worldmap_group = pygame.sprite.Group()
		worldmap_group.add(worldmap)

		# Map boundaries(tmx objects)
		map_objects = solgame.get_objects_from_tmx(tmx_data, 
											       Blocks)

		# Map kingdoms
		map_named_objects = solgame.get_objects_with_name_from_tmx(tmx_data, 
																   Blocks)

		# Map player
		images_with_directions = solgame.get_images_with_directions("sprites/playermap/", 8)	

		map_player = Player(game, "noroi", "noroi", game.WINDOW_WIDTH/2, game.WINDOW_WIDTH/2, images_with_directions)
		# 596 and 296 are coordinates near our Kingdom, WILL CHANGE!!
		map_player.set_position(596, 296)

		mp_group = pygame.sprite.Group()
		mp_group.add(map_player)

		direction = "down"

		change_x = 0
		change_y = 0

	# Events
	map_on = True
	while map_on:
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				game.quit_game()

			if event.type == pygame.KEYDOWN:
				if event.key == pygame.K_DOWN:
					direction = "down"
					change_y = 5
				if event.key == pygame.K_UP:
					direction = "up"
					change_y = -5
				if event.key == pygame.K_RIGHT:
					direction = "right"
					change_x = 5
				if event.key == pygame.K_LEFT:
					direction = "left"
					change_x = -5
				if event.key == pygame.K_m:
					return True, "stay"

			if event.type == pygame.KEYUP:
				if event.key == pygame.K_DOWN:
					change_y = 0
				if event.key == pygame.K_UP:
					change_y = 0
				if event.key == pygame.K_RIGHT:
					change_x = 0
				if event.key == pygame.K_LEFT:
					change_x = 0

		# for kingdom in KINGDOMS_COORDINATES:
		# 	x = KINGDOMS_COORDINATES[kingdom][0]
		# 	y = KINGDOMS_COORDINATES[kingdom][1]

		# 	if (map_player.rect.x <= x + 5 and map_player.rect.x >= x - 5 and
		# 		map_player.rect.y <= y + 5 and map_player.rect.y >= y - 5):
		# 		if kingdom == "home":
		# 			game.player.set_position(250, 250)
		# 			game.player.direction = "down"
		# 			return True

		# Check for bandits
		bandit_battle = game.encounter_bandits(map_player)
		if bandit_battle == "win":
			change_x = 0
			change_y = 0
		elif bandit_battle == "lose":
			return True, "stay"

		# Check if entered any of Kingdoms
		entered_kingdom = pygame.sprite.spritecollideany(map_player, map_named_objects)

		if entered_kingdom != None:
			if len(entered_kingdom.name.split(" ")) > 1:
				entered_kingdom.name = "_".join(entered_kingdom.name.split(" "))

			if entered_kingdom.name == "Tenebrae":
				return entered_kingdom.name, "leave"
			elif entered_kingdom.name == "Uwile_Castle":
				return entered_kingdom.name, "leave"

		map_player.set_direction()

		# Draw and update
		worldmap_group.draw(game.window)

		mp_group.draw(game.window)
		map_player.update([map_objects, [], []], direction)


		# Check if entered the story place
		story_result = game.entered_story_place("map", map_player)
		if story_result == False:
			# This means you lost
			return True, "lost"

		try:
			worldmap.update(map_player, 
							change_x, 
							change_y,
							map_objects,
							map_named_objects,
							game.story.place)
		except:
			worldmap.update(map_player, 
							change_x, 
							change_y,
							map_objects,
							map_named_objects,
							None)


		pygame.display.update()
		game.clock.tick(game.FPS)