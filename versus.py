"""
This is used for Versus game againts the computer with all characters.
"""

import os
import pygame
from battle import Battle
from colors import *

class Versus(object):
	def __init__(self, game):
		# Start loading
		with game.load():

			self.game = game
			self.window = self.game.window

			self.characters = []

			self.warriors = []
			self.enemies = []

			self.warrior_images = []
			self.enemy_images = []

			# Load player and add it to characters
			self.game.set_game(True)
			self.characters.append(self.game.player)

			# Original player skills
			# the skills that were loaded from the last save,
			# (doesn't mean allskills, just the skills he was using)
			self.original_player_skills = dict(self.game.player.skills)

			# Load all other unlocked characters
			self.unlocked_characters = self.get_unlocked_characters()
			self.get_npcs_from_files()

			# Images and texts
			self.title = self.game.display_text("Curse of Tenebrae", SILVER)
			self.battle_bg = pygame.image.load("images/vsbackground.png").convert()
			self.frame = pygame.image.load("images/vsframe.png").convert_alpha()
			self.warriors_text = self.game.display_text("Warriors", SILVER)
			self.enemies_text = self.game.display_text("Enemies", SILVER)
			# self.charselect_bg = pygame.image.load("IMAGE HERE!").convert()

			self.new_char_img_width = 100
			self.new_char_img_height = 115

			# Errors
			self.no_chosed_warriors = self.game.display_text(
										"You need to at least choose 1 warrior.",
										FIREBRICK
										)
			self.no_chosed_enemies = self.game.display_text(
										"You need to at least choose 1 enemy.",
										FIREBRICK
										)

		# Start
		self.characters_select()


	def get_unlocked_characters(self):
		"""
		Gets the names of unlocked characters
		and return a list with their names.
		"""
		characters = []

		with open("story/unlockedchars.txt") as fl:
			for line in fl:
				characters.append(line.strip())

		return characters

	def get_npcs_from_files(self):
		"""
		Creates the characters that are part of the 
		unlocked_characters list.
		"""

		npcs_filepath = "maps"

		npc_files = []
		for fl in os.listdir(npcs_filepath):
			if "npcs" in fl and ".txt" == os.path.splitext(fl)[1]:
				npc_files.append(fl)

		for npcfl in npc_files:
			with open(os.path.join(npcs_filepath, npcfl)) as nfl:
				npcs = nfl.readlines()

			for npcline in npcs:
				npc = self.game.make_npc(npcline)
				if npc is not None and npc.name in self.unlocked_characters:
					self.characters.append(npc)

	def get_rects_and_images(self):
		"""
		Returns tuple of two lists, first one contains all new character images,
		and the second one all rects of those images.
		"""

		character_images = []
		character_rects = []

		shift_x = 25
		shift_y = self.game.WINDOW_HEIGHT/2

		chars_per_row = 8
		chars_rowcount = 0

		shift_x_by = 100
		shift_y_by = 120

		for char in self.characters:
			# Set new smaller image
			newimg = pygame.transform.scale(char.warrior_image, 
										[self.new_char_img_width, self.new_char_img_height])
			character_images.append(newimg)

			# Set rect for that image
			newimg_rect = self.game.set_rect(newimg, shift_x, shift_y)
			character_rects.append(newimg_rect)

			shift_x += shift_x_by
			if chars_rowcount == chars_per_row:
				shift_x = 50
				shift_y += shift_y_by
				chars_rowcount = 0

			chars_rowcount += 1

		return character_images, character_rects

	def clear(self):
		"""
		It clears the chosed warriors and chosed enemies after the game.
		"""
		# Change images back to where they were
		self.change_image_direction()

		for char in self.warriors + self.enemies:
			if char in self.warriors:
				self.warriors.remove(char)
				self.warrior_images = []
			elif char in self.enemies:
				self.enemies.remove(char)
				self.enemy_images = []

			self.characters.append(char)

	def change_image_direction(self):
		"""
		Flips horizontally warrior images since all images face to the right,
		we need the warriors to face toward the left.
		"""

		new_warrior_images = []
		for warrior in self.warriors:
			newimg = pygame.transform.flip(warrior.warrior_image, True, False)
			warrior.warrior_image = newimg

	def set_chosed_chars_rects(self, charscount, shift_x, shift_y, shift_x_by):
		"""
		Returns a list with new rectangular points for the chosed warriors or enemies.
		"""
		new_rects = []

		for _ in range(charscount):
			rect = pygame.Rect(shift_x, shift_y, 
							   self.new_char_img_width, self.new_char_img_height)
			shift_x += shift_x_by

			new_rects.append(rect)

		return new_rects

	def characters_select(self):
		"""
		Displays the screen in which character select happens.
		"""
		errors = False
		error = None

		while True:
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					self.game.quit_game()
				if event.type == pygame.KEYDOWN:
					if event.key == pygame.K_l:
						self.game.show_skills()
					if event.key == pygame.K_ESCAPE:
						self.game.player.skills = dict(self.original_player_skills)
						return True
					if event.key == pygame.K_RETURN:
						if len(self.warriors) == 0:
							errors = True
							error = self.no_chosed_warriors
						elif len(self.enemies) == 0:
							errors = True
							error = self.no_chosed_enemies
						else:
							# Flip warrir images
							self.change_image_direction()
							# Start battle
							battle = Battle(self.game,
											self.warriors,
											self.enemies)
							battle.start_battle()
							# Clear warriors and enemies
							self.clear()

			# Get character image and rects
			self.character_images, self.character_rects = self.get_rects_and_images()

			# Display bg and title
			self.window.blit(self.battle_bg, [0, 0])
			self.window.blit(self.title, [self.game.center_text_x(self.title), 50])

			# Draw unlocked characters
			for char, charimg, imgrect in zip(self.characters, self.character_images, self.character_rects):
				self.window.blit(charimg,
								 [imgrect.x, imgrect.y])

				# Check if clicked character
				try:
					clicked_char, pressed_btn = self.game.clicked_surface_rect(imgrect, True, True)
					print pressed_btn
				except TypeError:
					clicked_char = False

				# Add clicked to warriors or to enemies group
				if clicked_char and pressed_btn[0] and len(self.warriors) < 3:
					self.characters.remove(char)
					self.warriors.append(char)
					self.warrior_images.append(charimg)
				elif clicked_char and pressed_btn[2] and len(self.enemies) < 3:
					self.characters.remove(char)
					self.enemies.append(char)
					self.enemy_images.append(charimg)

			# Draw enemies
			self.window.blit(self.enemies_text, 
							[self.game.WINDOW_WIDTH/1.3, 
							self.game.WINDOW_HEIGHT/5])
			enemy_rects = self.set_chosed_chars_rects(
								len(self.enemies),
								self.game.WINDOW_WIDTH/1.7,
								self.game.WINDOW_HEIGHT/4,
								100)

			for enemy, enemyimg, enemyrect in zip(self.enemies,
												  self.enemy_images,
												  enemy_rects):
				self.window.blit(enemyimg, [enemyrect.x, enemyrect.y])

				clicked_enemy = self.game.clicked_surface_rect(enemyrect)
				if clicked_enemy:
					# Remove from enemies and add to all characters
					self.enemies.remove(enemy)
					self.enemy_images.remove(enemyimg)
					self.characters.append(enemy)


			# Draw warriors
			self.window.blit(self.warriors_text, 
							[self.game.WINDOW_WIDTH/6, 
							self.game.WINDOW_HEIGHT/5])
			warrior_rects = self.set_chosed_chars_rects(
								len(self.warriors),
								20,
								self.game.WINDOW_HEIGHT/4,
								100)

			for warrior, warriorimg, warriorect in zip(self.warriors, 
													   self.warrior_images, 
													   warrior_rects):
				self.window.blit(warriorimg, [warriorect.x, warriorect.y])

				clicked_warrior = self.game.clicked_surface_rect(warriorect)
				if clicked_warrior:
					# Remove from warriors and add to all characters
					self.warriors.remove(warrior)
					self.warrior_images.remove(warriorimg)
					self.characters.append(warrior)

			# Draw errors if any
			if errors:
				self.window.blit(error,
								 [20, self.game.WINDOW_HEIGHT/1.1])

			# Update everything and set clock
			pygame.display.update()
			self.game.clock.tick(self.game.FPS)




