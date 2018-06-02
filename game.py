from __future__ import division
import sys
from contextlib import contextmanager
import os
from random import choice, randint
import time
from datetime import datetime
import threading
import itertools
import pygame
from pytmx.util_pygame import load_pygame
from sprites import Player, NPC, World, Blocks, Buildings, Shops
import inputbox
import solgame
import story
import solexceptions
from colors import *
from battle import Skill, Battle

class Game(object):
	def __init__(self, window):
		# Initialize pygame
		pygame.font.init()

		# Used for different part of the games with the
		# loading screen
		self.loaded = False

		# When loading a new game to check where the world map was
		# in the X and Y axis and which kingdom the user was
		self.loaded_kingdom = None
		self.loaded_world_x = None
		self.loaded_world_y = None

		# The seperator used in Curse of Tenebrae file
		self.file_seperator = "__"

		# Current story
		self.story = None

		# Window
		self.window = window
		self.WINDOW_WIDTH = window.get_width()
		self.WINDOW_HEIGHT = window.get_height()

		# Clock
		self.clock = pygame.time.Clock()
		self.FPS = 30

		# Groups
		self.player_group = pygame.sprite.Group()
		self.npc_group = pygame.sprite.Group()
		self.world_group = pygame.sprite.Group()
		self.objects_group = pygame.sprite.Group()
		self.buildings_group = pygame.sprite.Group()
		self.player_in_building_group = pygame.sprite.Group()
		self.shops_group = pygame.sprite.Group()
		self.clothes_group = pygame.sprite.Group()

		self.all_groups = [self.player_group,
						   self.npc_group,
						   self.world_group,
						   self.objects_group,
						   self.buildings_group,
						   self.player_in_building_group,
						   self.shops_group,
						   self.clothes_group]

		# Current Kingdom
		self.kingdom = None


		# Equipped clothes
		self.equipped_clothes = []

		# Objects
		self.world_objects = {}
		self.world_buildings = {}

		# Fonts
		self.small_font = pygame.font.Font("fonts/ringbearer/ringbearer.ttf", 15)
		self.npctalk_font = pygame.font.Font("fonts/ringbearer/ringbearer.ttf", 25)
		self.npctalk_font_big = pygame.font.Font("fonts/ringbearer/ringbearer.ttf", 50)

		# Load needed images
		# Inventory Background
		try:
			self.inventory_background = pygame.image.load("images/inventory.jpg").convert()
		except pygame.error:
			pass

		# Quotes
		self.sleeping_quotes = [
			"The woods are lovely, dark and deep. But I have promises to keep,\
			and miles to go before I sleep.",
			"The nicest thing for me is sleep, then at least I can dream.",
			"Sleep is the best meditation."]

		# NPC to talk to start the story mode
		self.oldman = NPC(self, "OldMan", 440, 450, "sprites/oldman.png", moves=False)
		self.npc_group.add(self.oldman)

		# Load skills
		self.load_skills()

		# Load NPC talks and questions, and answers
		self.load_npc_talks_and_questions()
		self.load_npc_answers()

	def start_story_mode(self):
		"""
		This is the function that holds the code that starts the story mode.
		"""

		curse_of_tenebrae = self.display_text("Curse of Tenebrae", SILVER,font_size="big")
		near_oldman = self.player.rect.colliderect(self.oldman.room)

		def display_start_story_mode():
			self.window.fill(BLACK)
			self.window.blit(curse_of_tenebrae,
							self.center_text(curse_of_tenebrae))

		display_start_story_mode = self.display_for_time(display_start_story_mode, 0)
		if near_oldman == 1:
			display_start_story_mode()
			self.story = story.Story(self, "birth_of_a_cursed_one")

			self.player.lead_x = 0
			self.player.lead_y = 0

	@contextmanager
	def load(self):
		"""
		Puts a loading screen until the data needed is loaded
		"""
		def loading_screen():
			loading_image = pygame.image.load("images/loading.jpg").convert()
			loading_text = self.display_text("Loading", WHITE)

			while not self.loaded:
				self.window.blit(loading_image,[0, 0])
				self.window.blit(loading_text,
							[self.WINDOW_WIDTH/2 - loading_text.get_width()/2,
							self.WINDOW_HEIGHT/2 - loading_text.get_height()/2])
				pygame.display.update()
				self.clock.tick(10)
			# When it ends set game loaded to false so it can be used
			# without being set explicitly on other parts of the game
			self.loaded = False

		try:
			loading_thread = threading.Thread(target=loading_screen,
											  name="loading")
			loading_thread.daemon = True
			yield loading_thread.start()
		finally:
			self.loaded = True

	def set_game(self, versus=False):
		"""
		Grabs all the data from the save file and assigns that data, to
		it's appropriate variables that'll be used in the game
		It's called set_game because most of the data belongs to the player
		but not all of it.

		Versus -- a bool if telling if set_game was called in the versus mode.
		"""

		character = {}

		# Grab attributes
		with open("save.txt", "r") as saved_file:
			lines = saved_file.readlines()

		try:
			for line in lines:
				attrs = line[:-1].split(self.file_seperator)
				# Assign attributes to the character dictionary
				if attrs[1].isdigit():
					# If it's a number, convert it into int
					attrs[1] = int(attrs[1])
				character[attrs[0]] = attrs[1]
		except IndexError as err:
			print err

		# Get images
		images_with_directions = solgame.get_images_with_directions(
													"sprites/{}/".format(character["character"]),
													character["images"])	
		
		# Create Player
		self.player = Player(self, character["name"], character["character"], 50, 50, images_with_directions)
		# Load attributes
		# self.player.set_name_and_character(character["name"], character["character"])
		self.player.set_position(character["x_pos"], character["y_pos"])
		self.player.level = character["level"]
		self.player.experience = character["experience"]
		self.player.can_carry = character["can_carry"]
		self.player.max_health = int(character["max_health"])
		self.player.max_magic = int(character["max_magic"])
		self.player.max_stamina = int(character["max_stamina"])
		self.player.health = int(character["health"])
		self.player.magic = int(character["magic"])
		self.player.stamina = character["stamina"]
		self.player.strength = character["strength"]
		self.player.defense = character["defense"]
		self.player.weight = character["weight"]

		character_items = eval(character["items"])
		character_chest = eval(character["chest"])
		for item in character_items:
			self.player.items[item] = character_items[item]

		for item in character_chest:
			self.player.chest[item] = character_chest[item]

		# Set clothes
		if character["cloth_on"] == "None":
			self.player.cloth_on = None
		else:
			self.player.cloth_on = character["cloth_on"]
		self.player.equipped_clothes = eval(character["equipped_clothes"])

		if (self.player.cloth_on != "None" and 
			self.player.cloth_on in self.player.equipped_clothes):
			# Wear clothes
			self.player.set_clothes(self.player.cloth_on)

		# Set skills
		self.player.set_allskills(eval(character["all_skills"]))
		self.player.set_skills(eval(character["skills"]))

		if not versus:
			# Caluclate and set weight
			self.player.calculate_weight()

			# Add in group
			self.player_group.add(self.player)

			# Set in which Kingdom the user was in, and the world X and Y
			self.loaded_kingdom = character["kingdom_in"]
			self.loaded_world_x = int(character["world_x"])
			self.loaded_world_y = int(character["world_y"])

			self.player.world_x = abs(int(character["world_x"]))
			self.player.world_y = abs(int(character["world_y"]))

			try:
				# Set the story
				self.story = story.Story(self, character["story"], True)
			except IOError as err:
				print "There is no such story '{}'.".format(character["story"])
				self.story = story.Story(self, "birth_of_a_cursed_one")

	def add_npcs(self, *npcs):
		"""
		Add's npcs to the npc sprite group
		"""

		for npc in npcs:
			self.npc_group.add(npc)

	def set_npcs_position_from_load(self):
		"""
		Sets the position of each npc according to the
		position of the world from the loaded data
		"""

		for npc in self.npc_group:
			npc.rect.x += self.loaded_world_x
			npc.rect.y += self.loaded_world_y
			npc.room.x += self.loaded_world_x
			npc.room.y += self.loaded_world_y

	def load_npc_talks_and_questions(self):
		"""
		Loads the NPC talks and questions and sets the to a dictionary 
		using their names
		"""
		# Load talks
		self.npc_talks = {}

		# Open talks file
		with open("sprites/talks.txt", "r") as talksfl:
			talks = talksfl.readlines()

		for npc_talk in talks:
			name, talk = npc_talk.split(self.file_seperator)
			self.npc_talks[name] = eval(talk)

		# Load questions
		self.npc_questions = {}

		with open("sprites/questions.txt", "r") as qfl:
			questions = qfl.readlines()

		for npc_q in questions:
			name, question = npc_q.split(self.file_seperator)
			self.npc_questions[name] = eval(question)

	def load_npc_answers(self):
		"""
		Loads all the NPC answers of our questions.

		Each NPC has some question we can ask them, and each question
		has its answer.
		"""

		self.npc_answers = {}

		# Open file
		with open("sprites/answers.txt", "r") as answersfl:
			for npc_answers in answersfl:
				npc_name, answers = npc_answers.split(self.file_seperator)
				self.npc_answers[npc_name] = eval(answers.strip())

	def make_npc(self, npcline, npc_list=None, npc_movinglist=None ,delimiter="__"):
		"""
		Makes an NPC ready for the game.
		npcline should be a line from a file containing all the npc data.
		"""

		def add_stoned_npc(name, image_path, x, y, can_chat, questions,
							   attributes, skills=None, warrior_image=None,
							   answers=None):
			"""
			Creates a stoned NPC.
			"""
			npc = NPC(self, name, x, y, image_path, 
					  moves=False, can_chat=can_chat, warrior_image=warrior_image)
			npc.set_questions(questions)
			npc.set_answers(answers)

			self.add_npcs(npc)

			if npc_list is not None:
				npc_list.append(npc)

			# Skills is a list containing skill names
			if skills:
				npc.set_skills(skills)

			# Set attributes
			npc.set_attributes(
				health=attributes["health"],
				magic=attributes["magic"],
				stamina=attributes["stamina"],
				max_health=attributes["max_health"],
				max_magic=attributes["max_magic"],
				max_stamina=attributes["max_stamina"],
				strength=attributes["strength"],
				defense=attributes["defense"],
				spell_strength=attributes["spell_strength"]
				)

			return npc

		def add_npc(name, images_path, images_count, x, y, talks,
						attributes, skills=None, warrior_image=None,
						answers=None):
			"""
			Creates a normal NPC that moves around.
			"""
			npc_images = solgame.get_images_with_directions(images_path, images_count)
			npc = NPC(self, name, x, y, npc_images, warrior_image=warrior_image)
			npc.set_talks(talks)
			npc.set_answers(answers)

			self.add_npcs(npc)

			if npc_list is not None and npc_movinglist is not None:
				npc_list.append(npc)
				npc_movinglist.append(npc)

			# Skills is a list containing skill names
			if skills:
				npc.set_skills(skills)

			# Set attributes
			npc.set_attributes(
					health=attributes["health"],
					magic=attributes["magic"],
					stamina=attributes["stamina"],
					max_health=attributes["max_health"],
					max_magic=attributes["max_magic"],
					max_stamina=attributes["max_stamina"],
					strength=attributes["strength"],
					defense=attributes["defense"],
					spell_strength=attributes["spell_strength"]
					)
			return npc

		# Make NPC
		try:
			npc_type, name, sprites, spritecount, x, y, talks_or_q, can_chat, \
			skills, attributes, warrior_image = npcline.split(delimiter)
		except ValueError:
			return False

		try:
			# Set talks or questions
			if talks_or_q == "talks":
				t_or_q = self.npc_talks[name]
			elif talks_or_q == "questions":
				t_or_q = self.npc_questions[name]
		except KeyError:
			t_or_q = []

		# Set answers
		try:
			npc_answers = self.npc_answers[name]
		except KeyError:
			npc_answers = None

		if npc_type == "normal":
			# Create NPC
			npc = add_npc(name, sprites, int(spritecount), int(x), int(y), t_or_q,
					eval(attributes), skills=eval(skills), warrior_image=warrior_image,
					answers=npc_answers)
			return npc
		elif npc_type == "stoned":
			# Create stoned NPC
			npc = add_stoned_npc(name, sprites, int(x), int(y), eval(can_chat), t_or_q,
						   eval(attributes), skills=eval(skills), warrior_image=warrior_image,
						   answers=npc_answers)
			return npc

		return None

	def create_npcs(self, filename, npc_list, npc_movinglist):
		"""
		Creates npcs from the NPC file.
		"""

		# Create NPCs
		# Open npcs file
		with open(filename) as npcfl:
			filelines = npcfl.readlines()

		# First lines contains info on how to create npcs
		# in a file so we don't include it
		filelines = filelines[1:]

		for line in filelines:
			self.make_npc(line, npc_list, npc_movinglist)

		# Set positions of NPCs
		self.set_npcs_position_from_load()

	def set_world(self, background):
		"""
		Create the world and set's it's position according
		to the position of the world from the loaded data
		"""

		# Create world and add to group
		self.world = World(background, 
						   self.window, 
						   self.objects_group,
						   self.buildings_group,
						   self.npc_group, 
						   self.player)
		self.world_group = pygame.sprite.Group()
		self.world_group.add(self.world)

		# Load the world according to world_X and world_Y from
		# the 'save' file
		self.world.rect.x = self.loaded_world_x
		self.world.rect.y = self.loaded_world_y

	def set_world_objects(self, tmx_data, blocks_sprite, builidings_sprite, shop_sprite=[]):
		"""
		Set's world objects and builidings

		Objects without a name go to the objects_group
		Objects with name(buildings, doors, etc..) go to their appropriate groups
		"""
		# Blocks
		self.objects_group = solgame.get_objects_from_tmx(tmx_data, 
														  blocks_sprite, 
														  [self.loaded_world_x, self.loaded_world_y])
		
		# Buildings
		self.buildings_group = solgame.get_objects_with_name_from_tmx(tmx_data, 
																	  builidings_sprite,
																	  [self.loaded_world_x, self.loaded_world_y],
																	  shop_sprite,
																	  self.world_buildings)

	def start_screen(self):
		"""
		Loads the Start Up screen of the game
		"""
		# Load image
		background = pygame.image.load("images/start2.jpg")

		# # Load music
		# pygame.mixer.music.load("sounds/start_again.mp3")
		# pygame.mixer.music.play(-1)

		# Set the font
		startscreen_font = pygame.font.Font("fonts/cardinal/Cardinal-Alternate.ttf", 75)
		startscreen_font_small = pygame.font.Font("fonts/cardinal/Cardinal-Alternate.ttf", 30)

		startscreen_title = startscreen_font.render("Curse of Tenebrae", 
													True, 
													WHITE)
		startscreen_start_exit_game = startscreen_font_small.render("Press Space To Start The Game or Press Esc To Quit", 
															   True, 
															   WHITE)
		start_on = True

		while start_on:
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					self.quit_game()
				if event.type == pygame.KEYDOWN:
					if event.key == pygame.K_SPACE:
						start_on = False
					if event.key == pygame.K_ESCAPE:
						self.quit_game()

			# Blit background
			self.window.blit(background, [0, 0])
			# Blit text
			self.window.blit(startscreen_title, 
						[self.WINDOW_WIDTH/2 - startscreen_title.get_width()/2, 
						self.WINDOW_HEIGHT - startscreen_title.get_height()*1.2])
			self.window.blit(startscreen_start_exit_game,
						[self.WINDOW_WIDTH/2 - startscreen_start_exit_game.get_width()/2,
						self.WINDOW_HEIGHT/1.23 - startscreen_start_exit_game.get_height()/2])

			pygame.display.update()
			self.clock.tick(10)

	def new_or_load(self):
		"""
		Asks user if they want to start a new game or load the previous one

		Uses the functions new_game and load_game and uses a file to save all the information
		about the user
		"""
		# Images
		background = pygame.image.load("images/menu2.jpg").convert()
		new_game_btn = pygame.image.load("images/newgame.png").convert()
		load_game_btn = pygame.image.load("images/loadgame.png").convert()
		versus_btn = pygame.image.load("images/versusbtn.png").convert()

		# Get button rects
		new_game_btn_rect = new_game_btn.get_rect()
		load_game_btn_rect = load_game_btn.get_rect()
		versus_btn_rect = versus_btn.get_rect()

		# Set x and y for button rect, since they're 0 and we need them
		# For button clicks
		new_game_btn_rect.x = load_game_btn_rect.x = versus_btn_rect.x = 50
		new_game_btn_rect.y = 50
		load_game_btn_rect.y = 125
		versus_btn_rect.y = 200


		# Clicking
		new_or_load_on = True
		while new_or_load_on:
			# Events
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					self.quit_game()
				# Also check if clicks N for newgame or L for loadgame
				if event.type == pygame.KEYDOWN:
					if event.key == pygame.K_n:
						# # New game
						new_game_called = True
						break
					elif event.key == pygame.K_l:
						load_game_called = True
						break

			# Check if it clicks new game or load game
			new_game_called = self.clicked_surface_rect(new_game_btn_rect)
			load_game_called = self.clicked_surface_rect(load_game_btn_rect)
			versus_called = self.clicked_surface_rect(versus_btn_rect)
			if new_game_called:
				self.new_game(background)
				return "game"
			elif load_game_called:
				self.load_game(background)
				return "game"
			elif versus_called:
				return "versus"

			# Draw and update screen
			self.window.blit(background, [0, 0])
			self.window.blit(new_game_btn, 
							[new_game_btn_rect.x, new_game_btn_rect.y])
			self.window.blit(load_game_btn, 
							[load_game_btn_rect.x, load_game_btn_rect.y])
			self.window.blit(versus_btn, 
							[versus_btn_rect.x, versus_btn_rect.y])

			pygame.display.update()
			self.clock.tick(15)

		# Check if user clicked new game or load game
		# to run the approprite function
		if new_game_called:
			self.new_game(background)
		elif load_game_called:
			self.load_game(background)

		# Stop the music from the last screen, since the game
		# Now starts
		# pygame.mixer.music.stop()

	def new_game(self, background):
		"""
		Functions used by 'new_or_load' to choose the character and newgame
		"""

		# New character creation
		new_character = {
			"name": None,
			"character": None,
			"images": 0,
			"x_pos": 300,
			"y_pos": 250,
			"level": 1,
			"experience": "0",
			"items": "{'Money': 100, 'Health Potions': 0, 'Magic Potions': 0}",
			"chest": "{}",
			"can_carry": 20,
			"max_health": 100,
			"max_magic": 50,
			"max_stamina": 150,
			"health": 100,
			"magic": 50,
			"strength": 30,
			"spell_strength": 20,
			"stamina": 100,
			"defense": 20,
			"weight": 0,
			"kingdom_in": "Tenebrae",
			"world_x": 0,
			"world_y": 0,
			"equipped_clothes": {},
			"cloth_on": None,
			"all_skills": [],
			"skills": ["punch", "block"],
			"story": None
		}

		# Load the images of the players that can be selected
		noroi = pygame.image.load("images/newchar/noroi.png").convert_alpha()
		curse = pygame.image.load("images/newchar/curse.png").convert_alpha()

		# Get rects of character images
		noroi_rect = noroi.get_rect()
		curse_rect = curse.get_rect()

		noroi_rect.x = self.WINDOW_WIDTH/5
		noroi_rect.y = self.WINDOW_HEIGHT/4
		curse_rect.x = self.WINDOW_WIDTH - (self.WINDOW_WIDTH/3)
		curse_rect.y = self.WINDOW_HEIGHT/4

		choosed_noroi = False
		choosed_curse = False

		# Rendering of text we will need to display
		choose_name_text = self.display_text("Choose Name", WHITE)
		choose_character_text = self.display_text("Choose Character", WHITE)

		# Get name from the user
		self.window.blit(background, [0, 0])
		self.window.blit(choose_name_text,
						[self.WINDOW_WIDTH/2 - choose_name_text.get_width()/2,
						 self.WINDOW_HEIGHT/2.5 - choose_name_text.get_height()/2])
		new_character["name"] = inputbox.ask(self.window, "")

		new_game_on = True
		while new_game_on:
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					self.quit_game()

			# Check if user clicked any of the characters
			# and create the new character with choosen options
			choosed_noroi = self.clicked_surface_rect(noroi_rect)

			choosed_curse = self.clicked_surface_rect(curse_rect)

			if choosed_noroi:
				new_character["character"] = "noroi"
				new_character["images"] = 8
				break
			if choosed_curse:
				new_character["character"] = "curse"
				new_character["images"] = 7
				break

			# Ask user to choose character
			# Display characters and update
			self.window.blit(background, [0, 0])
			self.window.blit(choose_character_text,
						[self.WINDOW_WIDTH/2 - choose_character_text.get_width()/2,
						 50])
			self.window.blit(noroi, [noroi_rect.x, noroi_rect.y])
			self.window.blit(curse, [curse_rect.x, curse_rect.y])

			pygame.display.update()
			self.clock.tick(15)

		# User choosed the name and character, now
		# create the new file with the given information

		# Create the new file
		with open("save.txt", "w") as new_game_file:
			for attr in new_character:
				line = "%s__%s\n" % (attr, new_character[attr])
				new_game_file.write(line)

	def load_game(self, background):
		"""
		Functions used by 'new_or_load' to load the last game

		Since the file exists we just put a loading screen and pass
		to the 'self' to run game, since there the file of the last save
		is read and the game is loaded from that previous save
		"""
		pass

	def quit_game(self):
		"""
		Quit's the game and uninitializes pygame modules safely
		"""
		pygame.quit()
		sys.exit(0)

	def save_game(self):
		"""
		Save the game setting all attributes on the save file 
		to the current value of those attributes in the game
		"""

		# List of attributes we will use
		attrs_names = ["images", "name", "character", "x_pos", "y_pos",
						"items", "chest", "level", "experience", "can_carry",
						"max_health", "max_magic", "health", "magic", "strength",
						"defense", "weight", "kingdom_in", "world_x", "world_y",
						"equipped_clothes", "cloth_on", "all_skills", "skills",
						"stamina", "max_stamina", "spell_strength", "story"]
		# Calculate and set weight of player before making the save
		self.player.calculate_weight()

		attrs = [self.player.largest_motion_image - 1,
				 self.player.name,
				 self.player.character,
				 self.player.rect.x,
				 self.player.rect.y,
				 self.player.items,
				 self.player.chest,
				 self.player.level,
				 self.player.experience,
				 self.player.can_carry,
				 self.player.max_health,
				 self.player.health,
				 self.player.max_magic,
				 self.player.magic,
				 self.player.strength,
				 self.player.defense,
				 self.player.weight,
				 self.player.kingdom_in,
				 self.world.rect.x,
				 self.world.rect.y,
				 self.player.equipped_clothes,
				 self.player.cloth_on,
				 self.player.allskills.keys(),
				 self.player.skills.keys(),
				 self.player.stamina,
				 self.player.max_stamina,
				 self.player.spell_strength,
				 self.story._name]

		# Make the new save
		with open("save.txt", "w") as save_file:
			for i in range(len(attrs)):
				line = "{}{}{}\n".format(attrs_names[i], self.file_seperator, attrs[i])
				save_file.write(line)

	def center_text_x(self, surface):
		return self.WINDOW_WIDTH/2 - surface.get_width()/2

	def center_text_y(self, surface):
		return self.WINDOW_HEIGHT/2 - surface.get_height()/2

	def center_text(self, surface):
		x = self.WINDOW_WIDTH/2 - surface.get_width()/2
		y = self.WINDOW_HEIGHT/2 - surface.get_height()/2
		return (x, y)

	def menu(self):
		"""
		Brings up the menu in which the player can exit the game, save the game,
		or go back at the start_screen
		"""

		# THE 80 BUGG!!

		menu_background = pygame.image.load("images/menucontrol.png").convert_alpha()

		# Buttons
		mainmenu_btn = pygame.image.load("images/mainmenubtn.png").convert()
		save_btn = pygame.image.load("images/savegame.png").convert()
		quit_btn = pygame.image.load("images/quitgame.png").convert()

		mainmenubtn_rect = mainmenu_btn.get_rect()
		save_btn_rect = save_btn.get_rect()
		quit_btn_rect = quit_btn.get_rect()

		menu_button_rects = [mainmenubtn_rect, save_btn_rect, quit_btn_rect]
		menu_buttons = [mainmenu_btn, save_btn, quit_btn]

		# Set rect to where they are
		change_y = 80
		for btn_rect in menu_button_rects:
			btn_rect.x = self.WINDOW_WIDTH/2 - btn_rect.width/2
			btn_rect.y = self.WINDOW_HEIGHT/3 + change_y
			change_y += 80

		# Menu text
		menu_text = self.display_text("Menu", BLACK, "big")

		# Game saved Text
		game_saved = False
		game_saved_text = self.display_text("Game Saved", BLACK)

		menu_on = True
		while menu_on:

			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					self.quit_game()
				elif event.type == pygame.KEYDOWN:
					if event.key == pygame.K_ESCAPE:
						return True

			# Check if any of the buttons were clicked
			mainmenu_clicked = self.clicked_surface_rect(mainmenubtn_rect)
			save_game_clicked = self.clicked_surface_rect(save_btn_rect)
			quit_game_clicked = self.clicked_surface_rect(quit_btn_rect)

			if mainmenu_clicked:
				return "mainmenu"
			elif save_game_clicked:
				game_saved = True
				self.save_game()
			elif quit_game_clicked:
				self.quit_game()

			# Draw Menu Background
			self.window.blit(menu_background, self.center_text(menu_background))

			# Draw text
			menu_background.blit(menu_text,
								[self.center_text_x(menu_text),
								self.WINDOW_HEIGHT/6])
			# If game was saved, tell the user
			if game_saved:
				menu_background.blit(game_saved_text,
									[self.WINDOW_WIDTH/2 - menu_background.get_width()/2,
									self.WINDOW_HEIGHT/2 - menu_background.get_height()/2])

			# Draw buttons
			for btn, rect in zip(menu_buttons, menu_button_rects):
				menu_background.blit(btn, [rect.x, rect.y-80])

			pygame.display.update()
			self.clock.tick(10)

	def _leaves_building(self, named_objects):
		"""
		Leaves the building in which we're currently in

		Checks if player is collided with the 'leave' object,
		if it is the we leave the building because it means we K_LEFT
		by the door xD
		"""

		leave = pygame.sprite.spritecollideany(self.player, named_objects)
		if leave != None and leave.name == "leave":
			return True
		else:
			return False

	def _open_shop(self, building, is_cloth_cloth=False):
		"""
		Asks if the user wants to buy or sell the items
		"""

		# Background image
		background = pygame.image.load("images/shop.jpg").convert()

		buy_text = self.display_text("Buy", BLACK)
		sell_text = self.display_text("Sell", BLACK)

		buy_rect = buy_text.get_rect()
		buy_rect.x = self.WINDOW_WIDTH/6
		buy_rect.y = self.WINDOW_HEIGHT/5

		sell_rect = sell_text.get_rect()
		sell_rect.x = self.WINDOW_WIDTH/6
		sell_rect.y = self.WINDOW_HEIGHT/4

		choose_to = None
		buy_or_sell = None

		shop_on = True
		while shop_on:
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					self.quit_game()

			for surface, rect, answer  in zip([buy_text, sell_text],
											  [buy_rect, sell_rect],
											  ["buy", "sell"]):
				clicked = self.clicked_surface_rect(rect)
				if clicked:
					if answer == "buy":
						buy_or_sell = "buy"
						break
					if answer == "sell":
						buy_or_sell = "sell"
						break

			if buy_or_sell != None:
				break

			# Draw and update everything
			self.window.blit(background, [0, 0])
			self.window.blit(buy_text,
							[self.WINDOW_WIDTH/6, self.WINDOW_HEIGHT/5])
			self.window.blit(sell_text,
							[self.WINDOW_WIDTH/6, self.WINDOW_HEIGHT/4])

			pygame.display.update()
			self.clock.tick(15)

		# Run buy or sell
		if buy_or_sell == "buy":
			self.buy_items(building, is_cloth_cloth)
		elif buy_or_sell == "sell":
			self.sell_items(building, is_cloth_cloth)

	def _get_shop_data(self, building, shop_items):
		# Shop Info File
		info_file_path = os.path.join(building.PATH, "{}.txt".format(building.name))
		with open(info_file_path, "r") as shop_fl:
			info = shop_fl.readlines()

		shop_data = []
		for item in info:
			# Get articles info
			image_file, description, cost = item[:-1].split("-")

			# Load items images
			image_path = os.path.join("images/items", image_file)
			item_image = pygame.image.load(image_path)

			# Load description text and cost
			description_text = self.display_text(description, BLACK)
			cost_text = self.display_text(cost, FIREBRICK)

			# Add to shop items that'll to be blitted later
			shop_items.append((item_image, description_text, cost_text))

			# Add to articles data
			item_name = image_file.split(".")[0].capitalize()
			shop_data.append((item_name, description, int(cost)))

		return shop_data

	def sell_items(self, building, clothshop=False):
		"""
		Displays all the user items that we can sell
		"""

		# Check if it's a cloth shop
		if clothshop:
			player_clothes_or_items = self.player.equipped_clothes
		else:
			player_clothes_or_items = self.player.items

		# List of surfaces that'll be blitted
		shop_items = []

		# Background
		shop_background = pygame.image.load("images/shop.jpg").convert()

		# Get articles data
		articles_data = self._get_shop_data(building, shop_items)

		# Set shop articles
		building.shop.set_articles(articles_data)

		# Background image and money image
		background = pygame.image.load("images/shop.jpg").convert()
		money_image = pygame.image.load("images/items/money.png")

		shift_item_x = self.WINDOW_WIDTH/6
		shift_item_y = self.WINDOW_HEIGHT/4
		shift_by = 50

		article_arrow = 0
		arrow_y = shift_item_y
		arrow_start = shift_item_y

		transaction_message = None

		sell_on = True
		while sell_on:
			# Check if it's a cloth shop
			if clothshop:
				player_clothes_or_items = self.player.equipped_clothes
			else:
				player_clothes_or_items = self.player.items

			# Check if player has items
			if player_clothes_or_items != {}:
				has_items = True
			else:
				has_items = False

			# Me lower per clothes since clothes jon lower krejt
			articles_to_sell = []
			for item in player_clothes_or_items:
				for article in articles_data:
					if item.split(" ")[0] == article[0] or item == article[0].lower():
						articles_to_sell.append(item)

			if clothshop:
				arrow_max = self.calculate_arrow_max(articles_to_sell, arrow_start)
			else:
				arrow_max = self.calculate_arrow_max(articles_to_sell[1:], arrow_start)

			# Events
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					self.quit_game()

				if event.type == pygame.KEYDOWN:
					if has_items:
						# Check if user has items
						if event.key == pygame.K_DOWN:
							article_arrow += 1
							arrow_y += 50
						elif event.key == pygame.K_UP:
							article_arrow -= 1
							arrow_y -= 50
						# Sell
						if event.key == pygame.K_RETURN:
							if clothshop:
								transaction_message = self.player.sell_clothes(building.shop, 
																			   item_names[article_arrow])
							else:
								transaction_message = self.player.sell(building.shop, 
																   item_names[article_arrow])
					if event.key == pygame.K_SPACE:
						building.shop.articles = []
						return True

			# Move the arrow
			# [1:] se pa money
			article_arrow, arrow_y = self.arrow_select(articles_to_sell,
													   article_arrow,
													   arrow_y,
													   arrow_start,
													   arrow_max)

			# Get all the items of users
			item_surfaces = []
			item_names = []
			item_images = []

			# Get money
			money_surface = self.display_text("Money: %s" % self.player.items["Money"],
											  BLACK)

			for item in player_clothes_or_items:
				if item == "Money":
					continue
				for article in articles_data:
					# Me lower se clothes are me lower
					if item.split(" ")[0] == article[0] or item == article[0].lower():
						# Get all the surfaces excepct money
						name_and_count = "%s: %s" % (item, player_clothes_or_items[item])
						surface = self.display_text(name_and_count, BLACK)
						name = item

						item_images_path = "images/items"
						image_path = os.path.join(item_images_path,
												  "{}.png".format(item.split(" ")[0].lower()))
						image = pygame.image.load(image_path).convert_alpha()

						# Add to lists
						item_surfaces.append(surface)
						item_names.append(name)
						item_images.append(image)

			# Draw and update everything
			self.window.blit(background, [0, 0])

			# Draw arrow
			pygame.draw.rect(self.window, FIREBRICK, 
							[shift_item_x - shift_by/3, arrow_y, 10, 10])

			# Draw money
			self.window.blit(money_image,
							[shift_item_x, self.WINDOW_HEIGHT/6])
			self.window.blit(money_surface,
							[shift_item_x + shift_by, self.WINDOW_HEIGHT/6])

			# Draw message
			if transaction_message != None:
				transaction_message_surface = self.display_text(transaction_message, BLACK)
			
				self.window.blit(transaction_message_surface,
								[self.center_text_x(transaction_message_surface),
								self.WINDOW_HEIGHT - transaction_message_surface.get_height() - shift_item_y])

			# Draw user items
			shift_y = shift_item_y
			for item, image in zip(item_surfaces, item_images):
				self.window.blit(image, [shift_item_x, shift_y])
				self.window.blit(item, [shift_item_x + shift_by, shift_y])
				shift_y += shift_by

			pygame.display.update()
			self.clock.tick(15)


	def buy_items(self, building, clothshop=False):
		"""
		Opens the shop showing what user can buy
		"""

		# List of surfaces that'll be blitted
		shop_items = []

		# Background
		shop_background = pygame.image.load("images/shop.jpg").convert()

		# Shop Info File
		articles_data = self._get_shop_data(building, shop_items)

		# Set shop articles
		building.shop.set_articles(articles_data)

		## ADD QWETQWG SOUND OF MONEY TE BUYING TOO, EDHE PER ERROR

		### Bone me shigjet
		articles = []
		for article in articles_data:
			articles.append(article[0])

		# Open shop
		article_arrow = 0

		# First item y_axis
		arrow_start = 100

		# Last item y_axis
		arrow_max = self.calculate_arrow_max(articles, 0)

		arrow_x = 140
		arrow_y = arrow_start

		transaction_message = None
		shop_on = True
		while shop_on:

			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					self.quit_game()

				if event.type == pygame.KEYDOWN:
					if event.key == pygame.K_SPACE:
						building.shop.articles = []
						return True
					if event.key == pygame.K_i:
						# Inventory
						self.show_profile()
					if event.key == pygame.K_RETURN:
						# Buys the item that was choosed
						transaction_message = self.player.buy(building.shop, 
															  current_article,
															  clothshop)

					# The arrow with which we move
					if event.key == pygame.K_DOWN:
						article_arrow += 1
						arrow_y += 50
					if event.key == pygame.K_UP:
						article_arrow -= 1
						arrow_y -= 50

			# print self.player.equipped_clothes
			# Get player money
			money = str(self.player.items["Money"])
			money_surface = self.display_text("Money: {}".format(money), BLACK)

			# Move the arrow
			article_arrow, arrow_y = self.arrow_select(articles, 
											 		   article_arrow, 
											 		   arrow_y, 
													   arrow_start, 
											 		   arrow_max)
			
			# The current article in which the rectangle is
			current_article = articles[article_arrow]

			# Draw and update everything
			self.window.blit(shop_background, [0, 0])

			# Draw the arrow
			pygame.draw.rect(self.window, FIREBRICK, [arrow_x, arrow_y, 10, 10])

			# Blit Money
			self.window.blit(money_surface, [150, self.WINDOW_HEIGHT - 120])

			# Blit transaction message
			if transaction_message != None:
				transaction_message_surface = self.display_text(transaction_message,
																BLACK)
				self.window.blit(transaction_message_surface, 
								[self.WINDOW_WIDTH/2.75, 
								self.WINDOW_HEIGHT - 120])

			# Blit all shop_items
			shift_x = 150
			shift_y = 100
			for ar_image, ar_description, ar_cost in shop_items:
				self.window.blit(ar_image, [shift_x, shift_y])
				self.window.blit(ar_description, [shift_x + ar_image.get_width() + 50, shift_y])
				self.window.blit(ar_cost, [shift_x+ar_description.get_width()+ 100, shift_y])
				shift_y += 50
			
			pygame.display.update()
			self.clock.tick(15)

	def enter_building(self, building):
		"""
		Gets the needed data of the building provided by 'name'
		and displays it until the player leaves it
		"""
		# Display loading screen until data is loaded
		self.load()

		# Set name of the building which is used in paths
		name = building.name

		# Set player last_building
		self.player.set_last_building(building)

		# See the 's' xD
		BUILDINGS_PATH = "buildings"

		# Get the path in which the building is
		tmx_path = os.path.join(BUILDINGS_PATH, name, "{}.tmx".format(name))
		image_path = os.path.join(BUILDINGS_PATH, name, "{}.png".format(name))

		# Load the tmx_data
		try:
			tmx_data = load_pygame(tmx_path)
			building_image = pygame.image.load(image_path)
		except IOError as err:
			print str(err)
			return True

		# Get objects
		objects_group = solgame.get_objects_from_tmx(tmx_data, 
													 Blocks)

		# Get objects with names
		named_objects = solgame.get_objects_with_name_from_tmx(tmx_data, 
															   Buildings, 
															   shop_sprite=Shops)

		# Check if building is a shop
		is_shop = False
		can_enter_shop = False

		if building.shop != None:
			is_shop = True

		is_cloth_cloth = False
		if building.cloth_shop:
			is_cloth_cloth = True

		### HOUSE
		# A variable to show if player is in bed
		can_sleep_in = None
		sleep_time_ok = False
		in_bed = None
		### HOUSE END

		# Add player to the group again since it was removed
		# When leaving the world function, and set position
		self.player_in_building_group.add(self.player)
		self.player.set_position(
					self.WINDOW_WIDTH/2, 
					self.WINDOW_HEIGHT/1.7)

		direction = "down"
		# Data loaded
		self.loaded = True

		building_on = True
		while building_on:

			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					self.quit_game()

				if event.type == pygame.KEYDOWN:
					if event.key == pygame.K_i:
						# Inventory
						self.show_profile()
					if event.key == pygame.K_DOWN:
						self.player.lead_y = 5
						# direction = "down"
					if event.key == pygame.K_UP:
						self.player.lead_y = -5
						# direction = "up"
					if event.key == pygame.K_RIGHT:
						self.player.lead_x = 5
						# direction = "right"
					if event.key == pygame.K_LEFT:
						self.player.lead_x = -5
					if event.key == pygame.K_SPACE:
						# Checks if the player is in the shop area
						# and if the player is open the shop
						if can_enter_shop:
							self._open_shop(building, is_cloth_cloth)

						# Check if we're in bed so we can sleep
						elif can_sleep_in != None and sleep_time_ok and in_bed != None:
							self.sleep()

						# Check if user is in the inventory
						elif enter_inventory:
							self.open_inventory()
					if event.key == pygame.K_c:
						# Show and change clothes
						self.show_clothes()
						self.player.lead_x = 0
						self.player.lead_y = 0

				if event.type == pygame.KEYUP:
					if event.key == pygame.K_DOWN:
						self.player.lead_y = 0
					if event.key == pygame.K_UP:
						self.player.lead_y = 0
					if event.key == pygame.K_RIGHT:
						self.player.lead_x = 0
					if event.key == pygame.K_LEFT:
						self.player.lead_x = 0

			# Check if the building is the house
			# So we can run lay_in_bed
			if building.name == "house":
				can_sleep_in, sleep_time_ok, in_bed = self.lay_in_bed(named_objects)

			# Check if player left the builiding by door
			# If it does, the we leave the building
			if self._leaves_building(named_objects):
				objects_group.empty()
				self.player_in_building_group.empty()
				self.player.rect.y += 5
				return True

			# Check if user is in the inventory area
			enter_inventory = self.in_inventory(named_objects)

			# Checks if player is entering the 'shop' area
			shop = pygame.sprite.spritecollideany(self.player, named_objects)
			if shop != None and shop.name == "shop":
				can_enter_shop = True
				enter_shop_msg = self.display_text("Press 'Space' to open shop.", FIREBRICK)
			else:
				can_enter_shop = False

			# Set direction
			direction = self.player.set_direction()

			# Draw everything
			self.window.blit(building_image, [0, 0])
			self.player_in_building_group.draw(self.window)
			self.player.update([objects_group, [] , []], direction)

			# Message to enter shop
			if can_enter_shop:
				self.window.blit(enter_shop_msg,
								[self.center_text_x(enter_shop_msg),
								self.WINDOW_HEIGHT/6])

			# Message to sleep in bed
			if can_sleep_in != None and in_bed != None:
				self.window.blit(can_sleep_in,
								[self.center_text_x(can_sleep_in),
								self.WINDOW_HEIGHT/6])


			# Message to open inventory
			if enter_inventory:
				self.window.blit(enter_inventory,
								[self.center_text_x(enter_inventory),
								self.WINDOW_HEIGHT/6])

			# Update
			pygame.display.update()
			self.clock.tick(self.FPS)

	def entered_building(self):
		"""
		Checks if user enteres a buildings, 
		then then runs 'enter_buildings' to get the data needed for that building
		and display it
		"""

		building = pygame.sprite.spritecollideany(self.player, self.buildings_group)
		if building != None:
			return building

	def show_profile(self):
		"""
		Show's the player profile with his profile information
		"""
		# Variables for positioning of surfaces and clicks
		shift_item_x = self.WINDOW_WIDTH/8
		shift_item_y = self.WINDOW_HEIGHT/5
		shift_by = 50

		# Name and images
		player_name = self.display_text(self.player.name, BLACK)

		# Check if player is wearing anything, if he is then we display him
		# with those clothes

		if self.player.cloth_on:
			player_image_path = os.path.join("images/profile", "{}.png".format(self.player.cloth_on))
		else:
			player_image_path = os.path.join("images/profile", "{}.png".format(self.player.character))
		player_image = pygame.image.load(player_image_path)

		money_image = pygame.image.load("images/items/money.png").convert_alpha()

		# Start game
		button_position = (0, 0)
		pressed_button = (0, 0, 0)

		inventory_on = True
		while inventory_on:

			# Events
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					self.quit_game()

				if event.type == pygame.KEYDOWN:
					if event.key == pygame.K_i:
						# We exit from the inventory
						return True

				button_position = pygame.mouse.get_pos()
				pressed_button = pygame.mouse.get_pressed()

			# Health and magic
			player_health = self.display_text("Health: {}".format(self.player.health), BLACK)
			player_magic = self.display_text("Magic: {}".format(self.player.magic), BLACK)

			# Items that'll be blitted
			item_images = []
			item_surfaces = []
			item_rects = []
			item_names = []

			# Money goes first, and it's always blitted
			shift_y = shift_item_y

			money = self.display_text("Money: %s" % str(self.player.items["Money"]), BLACK)
			money_rect = money.get_rect()
			money_rect.x, money_rect.y = shift_item_x + shift_by, shift_y
			shift_y += shift_by

			item_surfaces.append(money)
			item_images.append(money_image)
			item_rects.append(money_rect)
			item_names.append("Money")

			# If it doesn't have any of the items(Ex: 0 Health Potions)
			# we don't display them
			for item in self.player.items:
				if self.player.items[item] > 0 and item != "Money":
					## Item info
					name_and_count = "{}: {}".format(item,
													str(self.player.items[item]))
					item_surface = self.display_text(name_and_count, BLACK)

					# Set rect
					self.set_rect(item, shift_item_x + shift_by, shift_y)

					item_surfaces.append(item_surface)
					item_rects.append(item_rect)
					## Item image
					# Remove 'potions' part from the item name, since images don't
					# contain 'potions' in them
					item_img_name = item.split(" ")[0].lower()
					image_path = os.path.join("images/items", "{}.png".format(item_img_name))
					item_image = pygame.image.load(image_path).convert_alpha()

					item_images.append(item_image)
					item_names.append(item_img_name)

					shift_y += 50


			# Check which item was clicked		
			for item, item_rect, item_name in itertools.izip(item_surfaces, item_rects, item_names):
				clicked_item = self.clicked_surface_rect(item_rect)
				
				# Check if item was 'health' or 'magic'
				# So we can drink them
				if clicked_item:
					if item_name == "health":
						self.player.drink_health_potion()
					elif item_name == "magic":
						self.player.drink_magic_potion()

			# Draw and update everything
			self.window.blit(self.inventory_background, [0, 0])

			# Blit name and image
			self.window.blit(player_name, 
							[self.center_text_x(player_name), 
							player_name.get_height()])
			self.window.blit(player_image,
							[self.WINDOW_WIDTH - player_image.get_height(),
							self.center_text_y(player_image)])

			# Blit health and magic
			self.window.blit(player_health,
							[self.WINDOW_WIDTH/6,
							self.WINDOW_HEIGHT/8])
			self.window.blit(player_magic,
							[self.WINDOW_WIDTH/2.5,
							self.WINDOW_HEIGHT/8])

			# Blit all the items
			shift_y = self.WINDOW_HEIGHT/5
			for item_img, item in zip(item_images, item_surfaces):
				self.window.blit(item_img,
								[shift_item_x,
								shift_y])
				self.window.blit(item, 
								[shift_item_x + shift_by,
								shift_y])
				shift_y += shift_by

			pygame.display.update()
			self.clock.tick(15)

	def display_text(self, text, color, font_size="normal"):
		"""
		Returns a surface of text with the text and the color
		specified
		"""
		if font_size == "normal":
			message_surface = self.npctalk_font.render(text,
											  		   True,
											  	       color)
		elif font_size == "big":
			message_surface = self.npctalk_font_big.render(text,
											  		   	   True,
											  	           color)
		elif font_size == "small":
			message_surface = self.small_font.render(text,
													 True,
													 color)

		return message_surface

	# OLD xD
	# def clicked_srf(self, surface, surface_rect, pressed_button, button_position):
	# 	"""
	# 	Check if the given surface was clicked with mouse

	# 	NOT TRUE NOW:
	# 	# We need to check ourselves if the user clicked the mouse,
	# 	# since with this function it will check only if the mouse hovered
	# 	# into the surface to return true
	# 	"""
	# 	if pressed_button[0] == 1:
	# 		button_x_pos, button_y_pos = button_position[0], button_position[1]
	# 		if (button_x_pos >= surface_rect.x and 
	# 			button_x_pos <= surface_rect.x + surface.get_width() and
	# 			button_y_pos >= surface_rect.y and
	# 			button_y_pos <= surface_rect.y + surface.get_height()):
	# 			# Surface was clicked
	# 			return True
	# 		else:
	# 			return False
	# 	else:
	# 		return False


	def _npc_says(self, message):
		"""
		Grabs a message from the NPC Talks and returns a Surface
		of it to be used in the player_talks_with_npc function
		"""

		message_surface = self.npctalk_font.render(message, True, BLACK)
		return message_surface

	def player_talks_with_npc(self, npc):
		"""
		The function that displays what NPC got to say xD
		"""
		try:
			# Load the image that is used to display NPC message
			paper_background = pygame.image.load("images/paper.jpg").convert()
			npc_message = choice(npc.talks)

			while self.player.talking_with_npc:
				self.player.lead_x = 0
				self.player.lead_y = 0
				npc.talking = True
				
				for event in pygame.event.get():
					if event.type == pygame.QUIT:
						self.quit_game()

					if event.type == pygame.KEYDOWN:
						if event.key == pygame.K_RETURN:
							npc.talking = False
							self.player.talking_with_npc = False
							self.player.can_talk_to_npc = None
					
				message = self._npc_says(npc_message)
				self.window.blit(paper_background, [self.WINDOW_WIDTH/9, 500])
				paper_background.blit(message, 
									  [paper_background.get_width()/2 - message.get_width()/2,
									  paper_background.get_height()/2 - message.get_height()/2])
				pygame.display.update()
				self.clock.tick(10)
		except IndexError:
			pass

	def calculate_arrow_max(self, elements, start, shift=50):
		"""
		Calculates the max value that a group of surfaces will have
		being shifted, so the 'arrow' will work properly
		"""

		for element in elements:
			start += shift

		return start

	def arrow_select(self, elements, index, y_axis, start, end):
		"""
		Set's the arrow and the index to the element on which the arrow
		its on.
		"""

		if index == len(elements) or y_axis < start:
			y_axis = start
			index = 0
		elif index < 0 or y_axis < start:
			y_axis = end
			index = len(elements) - 1

		return index, y_axis

	def chat_with_npc(self, npc):
		"""
		Player is asked by one of the NPC Questions and he should provide an answer

		later: the answer will change something on the game like:
			# Player gets a new quest or item
			# Fights with the NPC etc...
		"""

		# A variable to keep track if the question was answered
		answered = False

		# Load chat image
		background = pygame.image.load("images/chat.jpg").convert()
		background_height = background.get_height()

		# Set arrow 
		question_shift = 40
		question_idx = 0

		question_start = self.WINDOW_HEIGHT - background_height/1.5
		question_max = self.calculate_arrow_max(npc.questions, question_start)
		question_y = question_start

		# Chose the answers
		question_surfaces = []
		for q in npc.questions:
			q_srf = self.display_text(q, BLACK)
			question_surfaces.append(q_srf)

		while 1:
			# Events
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					self.quit_game()

				if event.type == pygame.KEYDOWN:
					if event.key == pygame.K_DOWN:
						# Change arrow
						question_idx += 1
						question_y += 40
					if event.key == pygame.K_UP:
						# Change arrow
						question_idx -= 1
						question_y -= 40
					if event.key == pygame.K_RETURN:
						# Return the answer
						if answered:
							return npc.answers[question_idx]
						else:
							answered = True
							answer_srf = self.display_text(npc.answers[question_idx],
														   BLACK)

			# Move the arrow
			question_idx, question_y = self.arrow_select(npc.questions, 
											 		  question_idx, 
											 		  question_y, 
													  question_start, 
											 		  question_max)

			# Draw and update everything
			self.window.blit(background, 
							[self.center_text_x(background),
							self.WINDOW_HEIGHT - background_height])

			if answered:
				# Draw Answer
				self.window.blit(answer_srf,
								[self.WINDOW_WIDTH/3,
								self.WINDOW_HEIGHT - background_height/1.2])

			# Draw questions
			if not answered:
				# Draw Arrow
				pygame.draw.rect(self.window, FIREBRICK, 
								[self.WINDOW_WIDTH/8,
								question_y,
								10,
								10])

				question_shift_y = 0
				for q in question_surfaces:
					self.window.blit(q,
									[self.WINDOW_WIDTH/7,
									self.WINDOW_HEIGHT - background_height/1.5 \
									+ question_shift_y])
					question_shift_y += question_shift


			pygame.display.update()
			self.clock.tick(15)


	def sleep(self):
		"""
		Player sleeps, some health and magic is regenerated

		Add 20 Health and 10 Magic
		"""

		# Add health and magic
		health_to_add = self.player.max_health/5
		magic_to_add = self.player.max_magic/5

		# Add health
		if self.player.health < self.player.max_health:
			self.player.health += health_to_add
			if self.player.health > self.player.max_health:
				self.player.health = self.player.max_health

		# Add Magic
		if self.player.magic < self.player.max_magic:
			self.player.magic += magic_to_add
			if self.player.magic > self.player.max_magic:
				self.player.magic = self.player.max_magic

		# Sleeping text
		sleeping_z = self.display_text(
							choice(self.sleeping_quotes),
							WHITE)

		sleeping_hours = 0
		while sleeping_hours != 25:
			# Draw and update
			self.window.fill(BLACK)
			self.window.blit(sleeping_z, self.center_text(sleeping_z))

			pygame.display.update()
			self.clock.tick(15)

			sleeping_hours += 1

	def lay_in_bed(self, named_objects):
		"""
		Checks if user is 'colliding' with the bed
		When users is in the bed, we display 'Press Space to Sleep'
		"""

		# Check if there's a bed
		bed = None
		player_in_bed = None

		for obj in named_objects:
			if obj.name == "bed":
				bed = obj
				# Create new group with bed
				bed_group = pygame.sprite.Group()
				bed_group.add(bed)

		if bed == None:
			return None

		# Text we display when player in bed
		sleep_text = self.display_text("Press 'Space' to Sleep", FIREBRICK)

		# Check for collision
		player_in_bed = pygame.sprite.spritecollideany(self.player, bed_group)

		# Check for the time, see if user can sleep
		time_now = datetime.now().minute

		# Time remained to sleep
		time_remained = (self.player.sleep_time + 10) - time_now

		if time_now <= self.player.sleep_time + 10 and time_now >= self.player.sleep_time:
			# sleep_text = self.display_text("You can't sleep right now", FIREBRICK)
			sleep_text = self.display_text("You can't sleep in %d minutes" % time_remained, FIREBRICK)
			return sleep_text, False, player_in_bed

		# If player is in bed return the text so we can display it
		if player_in_bed != None:
			return sleep_text, True, player_in_bed
		else:
			return None		

	def in_inventory(self, named_objects):
		"""
		Returns text if player is in the inventory area
		"""
		# Get inventory from the named objects
		inventory_group = pygame.sprite.Group()
		inventory = None

		for obj in named_objects:
			if obj.name == "inventory":
				inventory = obj
				inventory_group.add(inventory)
				break

		if inventory == None:
			return None

		# Check if the user is in the inventory
		inventory_collision = pygame.sprite.spritecollideany(self.player, inventory_group)

		# Text to be displayed
		inventory_text = self.display_text("Press 'Space' to open inventory", FIREBRICK)

		if inventory_collision:
			return inventory_text
		else:
			return None

		inventory_group.empty()

	def open_inventory(self):
		"""
		Opens the inventory checst of player, in which he can place
		the things he want, so his 'carry_weight' will be lower
		"""

		# Inventory background
		background = pygame.image.load("images/chest.jpg").convert()

		items_text = self.display_text("Items", BLACK)
		inventory_text = self.display_text("Inventory", BLACK)

		button_pressed = (0, 0, 0)
		button_position = (0, 0)

		shift_item_x = 50
		shift_item_y = 100

		shift_chest_x = self.WINDOW_WIDTH - shift_item_x*5

		while 1:
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					self.quit_game()

				if event.type == pygame.KEYDOWN:
					if event.key == pygame.K_SPACE:
						return True

				button_position = pygame.mouse.get_pos()
				button_pressed = pygame.mouse.get_pressed()

			# Get items from player
			player_items_surfaces = []
			for item in self.player.items:
				item_surface = self.display_text(
									"{}: {}".format(item, self.player.items[item]),
									BLACK)
				player_items_surfaces.append(item_surface)

			# Get items from chest inventory
			chest_items_surfaces = []
			for item in self.player.chest:
				item_surface = self.display_text(
									"{}: {}".format(item, self.player.chest[item]),
									BLACK)
				chest_items_surfaces.append(item_surface)

			# Get rects of items
			player_rects = []
			shift_x = shift_item_x
			shift_y = shift_item_y
			for item in player_items_surfaces:
				item_rect = item.get_rect()
				item_rect.x = shift_x
				item_rect.y = shift_y
				shift_y += 50
				player_rects.append(item_rect)

			chest_rects = []
			shift_x = shift_chest_x
			shift_y = shift_item_y
			for item in chest_items_surfaces:
				item_rect = item.get_rect()
				item_rect.x = shift_x
				item_rect.y = shift_y
				shift_y += 50
				chest_rects.append(item_rect)

			# Get names and values of items of player
			player_items = []
			for item in self.player.items:
				# Add the item name and value
				player_items.append((item, self.player.items[item]))

			# Get names and values of items of chest
			chest_items = []
			for item in self.player.chest:
				# Add the item name and value
				chest_items.append((item, self.player.chest[item]))


			# Check if user clicked any player items
			for item_surface, item_rect, item in zip(player_items_surfaces, player_rects, player_items):

				clicked_item = self.clicked_surface_rect(item_rect)

				if clicked_item:
					# The clicked item
					item_name, item_value = item[0], item[1]

					if item_value == 0:
						pass
					elif item_value > 0:
						# Set them
						self.player.items[item_name] -= 1

						try:
							self.player.chest[item_name] += 1
						except KeyError:
							self.player.chest[item_name] = 1

			# # Check if user clicked any chest items
			for citem_surface, citem_rect, citem in zip(chest_items_surfaces, chest_rects, chest_items):
				cclicked_item = self.clicked_surface_rect(citem_rect)
				if cclicked_item:
					# The clicked item
					citem_name, citem_value = citem[0], citem[1]

					if citem_value == 0:
						pass
					elif citem_value > 0 and self.player.weight < self.player.can_carry:
						# Set them
						self.player.chest[citem_name] -= 1
						try:
							self.player.items[citem_name] += 1
						except KeyError:
							self.player.items[citem_name] = 1

			# Calculate and set weight of player
			self.player.calculate_weight()


			# Draw and update everything
			self.window.blit(background, [0, 0])

			# Draw items | inventory text
			self.window.blit(items_text,
							[self.WINDOW_WIDTH/4,
							self.WINDOW_HEIGHT/20])

			self.window.blit(inventory_text,
							[self.WINDOW_WIDTH/1.5,
							self.WINDOW_HEIGHT/20])

			# Draw items from player
			shift_x = shift_item_x
			shift_y = shift_item_y
			for item in player_items_surfaces:
				self.window.blit(item, [shift_x, shift_y])
				shift_y += 50

			# Draw items from chest
			shift_x = shift_chest_x
			shift_y = shift_item_y
			for item in chest_items_surfaces:
				self.window.blit(item, [shift_x, shift_y])
				shift_y += 50


			pygame.display.update()
			self.clock.tick(self.FPS)

	def show_clothes(self):
		"""
		Shows an inventory of all the player clothes and the player
		can wear on unwear clothes by clicking on them
		"""

		# Images path
		images_path = "images/items"

		# Shifts
		shift_text_y = 50

		shift_cloth_x = 100
		shift_cloth_y = 100

		shift_cloth_x_end = self.WINDOW_WIDTH - shift_cloth_x*2

		shift_by = 60

		# Texts
		clothes_text = self.display_text("Clothes", BLACK)
		equipped_text = self.display_text("Equipped", BLACK)

		button_pressed = (0, 0, 0)
		button_position = (0, 0)

		# Equipped cloth by player
		equipped_cloth = self.player.cloth_on

		while True:
			# Events
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					self.quit()

				if event.type == pygame.KEYDOWN:
					if event.key == pygame.K_c:
						# If C is pressed then we do nothing
						# so no change happens
						return True
					if event.key == pygame.K_RETURN:
						# If enter is pressed the we change clothes
						self.player.set_clothes(equipped_cloth)
						self.player.cloth_on = equipped_cloth
						return True

				# Button press and position
				button_pressed = pygame.mouse.get_pressed()
				button_position = pygame.mouse.get_pos()

			# Get clothe surfaces, names and rects
			clothes = self.player.equipped_clothes

			# Get eqquiped cloth
			if equipped_cloth != None:
				equipped_cloth_surface = pygame.image.load(	
											os.path.join(
												images_path, 
												"{}.png".format(equipped_cloth)
												)
											)
				equipped_cloth_rect = equipped_cloth_surface.get_rect()
				equipped_cloth_rect.x = shift_cloth_x_end
				equipped_cloth_rect.y = shift_cloth_y

			# Clothes of player
			clothes_names = []
			clothes_surfaces = []
			clothes_rects = []

			# Get needed data for display
			shift_y = shift_cloth_y
			for cloth in clothes:
				# Don't add the eqquiped cloth
				if cloth == equipped_cloth:
					continue

				# Add name
				clothes_names.append(cloth)

				# Add surface image
				fullpath = os.path.join(images_path, 
										"{}.png".format(cloth))
				image = pygame.image.load(fullpath)
				clothes_surfaces.append(image)

				# Add rect
				image_rect = self.set_rect(image, shift_cloth_x, shift_y)
				clothes_rects.append(image_rect)

				# Make shift
				shift_y += shift_by


			if equipped_cloth != None:
				# Check if equipped cloth is selected, to remove clothes
				clicked_equipped = self.clicked_surface_rect(equipped_cloth_rect)
				if clicked_equipped:
					equipped_cloth = None

			# Check if any of the surfaces is clicked
			for cloth_surface, cloth_rect, name in zip(clothes_surfaces,
													   clothes_rects,
													   clothes_names):
				clicked = self.clicked_surface_rect(cloth_rect)
				if clicked:
					# Put the selected cloth as equipped
					equipped_cloth = name

			# Draw and update everything
			# Draw background
			self.window.blit(self.inventory_background, [0, 0])

			# Draw texts
			self.window.blit(clothes_text, 
							[shift_cloth_x, shift_text_y])
			self.window.blit(equipped_text,
							[shift_cloth_x_end, shift_text_y])

			# Draw eqquiped cloth
			if equipped_cloth != None:
				try:
					self.window.blit(equipped_cloth_surface,
									[equipped_cloth_rect.x,
									equipped_cloth_rect.y])
				except UnboundLocalError:
					pass

			# Draw clothes
			for cloth, rect in zip(clothes_surfaces, clothes_rects):
				self.window.blit(cloth, [rect.x, rect.y])

			pygame.display.update()
			self.clock.tick(15)

	# Skills
	def load_skills(self):
		"""
		Loads the skills from the skill file and makes them ready for access
		returning a dictionary which contains the skill name as key and skill
		attrs as value.
		"""

		skills_file_path = "battle/skills.txt"

		self.skills = {}

		# Open skill file
		with open(skills_file_path) as skillfl:
			skillslines = skillfl.readlines()

		# We do this slice becuase the first line is 'help'
		# on how skills are saved in the skills.txt file
		skillslines = skillslines[1:]
		
		for skill in skillslines:
			try:
				# Split the skill
				name, image, skilltype, entype, dmgdef, description, cost, \
				countdown, skillrange = skill.split(self.file_seperator)
			except ValueError as err:
				raise solexceptions.SkillError(str(err))

			# Save it on the skills dictionary using a lowercase version of name
			# since we'll mostly use lowercase when creating new skills
			# (we need a name to create new skills xD)
			self.skills[name.lower()] = (name, image, skilltype, entype, 
										int(dmgdef), description, int(cost), 
										int(countdown), skillrange[:-1])

		return self.skills

	def set_rects(self, surfaces, x, y, shfit_x=0, shift_y=0, dictionary=False):
		"""
		Set rects for the given surfaces.
		"""

		if not dictionary:
			for srf in surfaces:
				surface_rect = surface.get_rect()
				# Set points
				surface_rect.x = x
				surface_rect.y = y
				# Shift
				x += shift_x
				y += shift_y
		else:
			for srf in surfaces.itervalues():
				surface_rect = surface.get_rect()
				# Set points
				surface_rect.x = x
				surface_rect.y = y
				# Shift
				x += shift_x
				y += shift_y

	def set_rect(self, surface, x, y, warriorect=False):
		"""
		Sets rect for a single surface, if warriorect is True,
		it changes not the rect of that sprite, but the warrior_rect
		variable.
		"""

		if not warriorect:
			surface_rect = surface.get_rect()
			surface_rect.x = x
			surface_rect.y = y

			return surface_rect
		else:
			rect = surface.warrior_rect
			rect.x = x
			rect.y = y

			return rect

	def set_sprite_rects(self, sprites, x, y, shift_x=0, shift_y=0, dictionary=False):
		"""
		Sets rects for the given sprites according to the given data.
		The 'sprites' argument by default should be a list of sprites
		but if a dictionary of sprites is given the 'dictionary' argument
		should be set to True
		"""

		if not dictionary:
			for sprt in sprites:
				# Set points
				sprt.rect.x = x
				sprt.rect.y = y
				# Shift
				x += shift_x
				y += shift_y
		else:
			for sprt in sprites.itervalues():
				# Set points
				sprt.rect.x = x
				sprt.rect.y = y
				# Shift
				x += shift_x
				y += shift_y

	def clicked_surface(self, srf, pressedbutton=False, rightclick=False):
		"""
		Check if a skill was clicked and returns True if yes,
		False otherwise, if pressedbutton is True it return which button was pressed.
		If rightclick if True it returns True for right clicks on surfaces too.
		"""

		button_pressed = pygame.mouse.get_pressed()
		button_pos = pygame.mouse.get_pos()

		if not rightclick:
			if button_pressed[0]:
				clicked = srf.rect.collidepoint(button_pos)
				if clicked and pressedbutton:
					return True, button_pressed
				elif clicked:
					return True
		else:
			if button_pressed[0] or button_pressed[2]:
				clicked = srf.collidepoint(button_pos)
				if clicked and pressedbutton:
					return True, button_pressed
				elif clicked:
					return True

		return False

	def clicked_surface_rect(self, rect, pressedbutton=False, rightclick=False):
		"""
		Check if the the given rect was clicked,
		return True if yes and False otherwise
		"""

		button_pressed = pygame.mouse.get_pressed()
		button_pos = pygame.mouse.get_pos()

		if not rightclick:
			if button_pressed[0]:
				clicked = rect.collidepoint(button_pos)
				if clicked and pressedbutton:
					return True, button_pressed
				elif clicked:
					return True
		else:
			if button_pressed[0] or button_pressed[2]:
				clicked = rect.collidepoint(button_pos)
				if clicked and pressedbutton:
					return True, button_pressed
				else:
					return True

		return False

	def show_skills(self):
		"""
		Shows the skills the user has and lets him change the skills that
		he wants to use
		"""

		# Frame image
		frame = pygame.image.load("images/roseframe.png").convert_alpha()

		# Shifts
		shift_x_by = 100

		# Using skills shifts
		ushift_x = self.WINDOW_WIDTH/4
		ushift_y = 10
		# Attributes shifts
		attrshift_y = self.WINDOW_HEIGHT-50
		attrshift_x = 50
		# All skills shifts
		ashift_x = 50
		ashift_y = 150

		# Use to display the skill attr bar
		hovering_over = None

		skills_on = True
		while skills_on:
			# Events
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					self.quit_game()

				if event.type == pygame.KEYDOWN:
					if event.key == pygame.K_l:
						return True

			# Draw and update everything
			self.window.blit(self.inventory_background, [0, 0])

			### USING SKILLS
			# Set using_skills rects
			self.set_sprite_rects(self.player.skills, ushift_x, ushift_y, shift_x=shift_x_by, dictionary=True)

			# Draw using skills
			using_skills_to_change = None
			for skillname in self.player.skills:
				skill = self.player.skills[skillname]
				# Draw image
				self.window.blit(skill.image, [skill.rect.x, skill.rect.y])
				# Check if it's hovering over any of the skills
				hovering = skill.rect.collidepoint(pygame.mouse.get_pos())
				if hovering:
					hovering_over = skill

				# Check if one of the using skills was clicked
				clicked_using_skill = self.clicked_surface(skill)
				if clicked_using_skill:
					using_skills_to_change = skill

			# Make the change if a using skill was clicked
			if using_skills_to_change:
				skill_name = using_skills_to_change.name.lower()
				# Remove it from using skills
				self.player.skills.pop(skill_name)
				# Add it to all skills
				self.player.allskills[skill_name] = using_skills_to_change

			### Draw frames
			shift_x = ushift_x
			for i in range(4):
				# Draw frame
				self.window.blit(frame, [shift_x, ushift_y])
				shift_x += shift_x_by

			# Draw seperator
			pygame.draw.line(self.window, (20,20,20), [25, 125], [self.WINDOW_WIDTH-25, 125], 2)

			### ALL SKILLS
			# Set skills rects and draw skills
			iterator = 0
			shift_x = ashift_x
			shift_y = ashift_y
			skill_to_change = None

			for skillname in self.player.allskills:
				# Assign skill object to this variable
				skill = self.player.allskills[skillname]

				# Iterator is used to help in displaying
				# only 7 skills per row, so we change the shift_y
				# and set shift_x to the beggining in a new row
				if iterator == 7:
					shift_x = ashift_x
					shift_y += 120

				# Change rects
				skill.rect.x = shift_x
				skill.rect.y = shift_y

				# Make shifts
				shift_x += shift_x_by
				iterator += 1

				# Draw
				self.window.blit(skill.image, [skill.rect.x, skill.rect.y])

				# Check if it's player is hovering over any of the skills
				hovering = skill.rect.collidepoint(pygame.mouse.get_pos())
				if hovering:
					hovering_over = skill

				# Check if one of the allskills if being clicked to set it as 
				# 'using' skill
				clicked_skill = self.clicked_surface(skill)

				if clicked_skill:
					# Check if any of all skills is clicked
					skill_to_change = skill

			# If any of the all skills was clicked
			# remove it from all skills and add it to using skills
			if skill_to_change:
				# Check if using skills len is 4
				# If it is we don't assign it
				if len(self.player.skills) == 4:
					pass
				else:
					skill_name = skill_to_change.name.lower()
					# Remove from all skills
					self.player.allskills.pop(skill_name)
					# Add to using skills
					self.player.skills[skill_name] = skill_to_change

			# Draw seperator
			pygame.draw.line(self.window, 
							(20,20,20), 
							[25, self.WINDOW_HEIGHT-70], 
							[self.WINDOW_WIDTH-25, self.WINDOW_HEIGHT-70],
							2)

			### Draw skill bar
			if hovering_over:
				# Get attributes
				name = self.display_text(hovering_over.name, BLACK)
				skilltype = self.display_text(hovering_over.skilltype, BLACK)
				entype = self.display_text(hovering_over.entype, BLACK)
				dmgdef = self.display_text(str(hovering_over.dmgdef), BLACK)

				# Draw attributes
				self.window.blit(name, [attrshift_x, attrshift_y])
				self.window.blit(skilltype, [self.WINDOW_WIDTH/2, attrshift_y])
				self.window.blit(entype, [self.WINDOW_WIDTH/1.5, attrshift_y])
				self.window.blit(dmgdef, [self.WINDOW_WIDTH/1.2, attrshift_y])




			pygame.display.update()
			self.clock.tick(15)

	def display_for_time(self, func, seconds):
		"""
		A decorator used to run a function for the given time.
		Used with functions that display surfaces on Window Surface.
		"""

		def inner_func(*args, **kwargs):
			timenow = time.time()
			time_to_end = timenow + seconds

			while timenow < time_to_end:
				func(*args, **kwargs)
				timenow = time.time()
				pygame.display.update()
				self.clock.tick(13)
		return inner_func

	def entered_story_place(self, placetype, player):
		"""
		Checks if the the player entered the story
		place so we ask him if he wants to start the story,
		or begin it ourselves.
		"""

		try:
			if self.story is not None and self.story.terrain == placetype:
				self.window.blit(self.story.hint, [self.story.place.x, self.story.place.y])

				onit = player.rect.colliderect(self.story.place)
				if onit:
					story_result = self.story.begin_story()
					return story_result
		except AttributeError as err:
			print str(err)

	def show_story_board(self):
		"""
		Shows an image containing information about the current story.
		"""
		try:
			# Get story text
			name = self.display_text(self.story.name, BLACK)
			description = self.display_text(self.story.description, BLACK, font_size="small")

			story_on = True
		except AttributeError:
			message = self.display_text("No current Story!", BLACK)
			story_on = False

		while True:
			# Events
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					self.quit_game()

				if event.type == pygame.KEYDOWN:
					if (event.key == pygame.K_RETURN or
						event.key == pygame.K_ESCAPE):
						return True

			# Draw and update everything
			self.window.blit(self.inventory_background, [0, 0])

			if story_on:
				self.window.blit(name, [50, 50])
				self.window.blit(description, [30, 100])
			else:
				self.window.blit(message, [50, 50])

			pygame.display.update()
			self.clock.tick(15)

	def show_kingdom_map(self):
		"""
		Displays the map of the current kingdom.
		"""
		# Get needed data to set user point of where he is
		kingdom_width = self.world.image.get_width()
		kingdom_height = self.world.image.get_height()

		width_division = kingdom_width/self.WINDOW_WIDTH
		height_division = kingdom_height/self.WINDOW_HEIGHT

		player_name = self.display_text(self.player.name, BLACK, font_size="small")

		while True:
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					self.quit_game()
				if event.type == pygame.KEYDOWN and event.key == pygame.K_k:
					return True

			
			x_axis = self.player.world_x+self.player.rect.x+self.player.image.get_width()/2
			y_axis = self.player.world_y+self.player.rect.y+self.player.image.get_height()/2

			player_map_xaxis = x_axis/width_division
			player_map_yaxis = y_axis/height_division

			# Display and update
			self.window.blit(self.kingdom.map, [0, 0])
			pygame.draw.circle(self.window, FIREBRICK, 
							  [int(player_map_xaxis), int(player_map_yaxis)], 
							  5)

			pygame.display.update()
			self.clock.tick(15)

	def set_next_story(self):
		"""
		Sets the next story if the current one
		is finished.
		"""

		with open("story/wholestory.txt", "r") as fl:
			stories = fl.readlines()

		for story in stories:
			storyname = story.strip()
			try:
				if storyname == self.story._name:
					# Set the next story
					current_story_index = stories.index(story)
					try:
						next_story = stories[current_story_index+1]
						self.story = story.Story(next_story)
						return True
					except IndexError:
						self.story = "No Stories!"
						return False
			except AttributeError:
				return False

	def show_help(self):
		"""
		Displays a scroll containing help on how to play the game.
		"""

		background = pygame.image.load("images/help.png").convert_alpha()

		help = [
			"===========World",
			"M - Open Map",
			"K- Open Kingdom Map",
			"Q - Open Story board",
			"L - Open skills",
			"I - Open inventory",
			"C - Open Clothes inventory",
			"Space - Talk to an NPC when near him/her",
			"ESC - Open Menu",
			"===========Battle",
			"Space - Next Turn",
			"Any Key - Clear chosed skill and warrior of selected character",
			]

		help_surfaces = []
		for helpline in help:
			help_surfaces.append(
					self.display_text(helpline, BLACK, font_size="small")
					)

		shift_x = self.WINDOW_WIDTH/6

		while True:
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					self.quit_game()
				if event.type == pygame.KEYDOWN:
					if event.key == pygame.K_h or event.key == pygame.K_ESCAPE:
						return True
			
			# Draw and update everything
			self.window.blit(background, [0, 0])


			shift_y = self.WINDOW_HEIGHT/18
			shift_by = 50
			for helptext in help_surfaces:
				self.window.blit(helptext,
								 [shift_x,
								  shift_y])
				shift_y += shift_by

			pygame.display.update()
			self.clock.tick(15)

	def unlock_character(self, name):
		"""
		Adds a character to the unclocked characters file.
		"""

		with open("story/unlockedchars.txt", "a") as fl:
			fl.write("{}\n".format(name))

	def lock_character(self, name):
		"""
		Removes a character from the unclocked characters file.
		"""

		with open("story/unlockedchars.txt", "r") as fl:
			unlocked_chars = fl.readlines()

		try:
			unlocked_chars.remove("{}\n".format(name))
		except ValueError:
			print "'{}' is not in the characters list.".format(name)

		# Write to file

		with open("story/unlockedchars.txt", "w") as fl:
			for char in unlocked_chars:
				fl.write(char)

	def encounter_bandits(self, player, encountering_bandit_rate=200):
		"""
		Checks if player encountered any bandits while moving
		on the map.
		"""
		bandit_id = randint(0, encountering_bandit_rate)

		if player.lead_x != 0 or player.lead_y != 0:
			if bandit_id == randint(0, encountering_bandit_rate):
				with self.load():
					bandit_text = self.display_text("Encountered Bandits!!", 
													BLACK)

					if randint(1, 200) > 190:
						num_of_bandits = 2
					else:
						num_of_bandits = 1

					with open("battle/bandits.txt") as fl:
						bandit_lines = fl.readlines()

					bandits = []
					for _ in range(0, num_of_bandits):
						bandit_line = choice(bandit_lines)
						bandt = self.make_npc(bandit_line)
						bandits.append(bandt)

				encountered_msg = True
				while encountered_msg:
					for event in pygame.event.get():
						if event.type == pygame.QUIT:
							self.quit_game()
						if event.type == pygame.KEYDOWN:
							if event.key == pygame.K_SPACE:
								encountered_msg = False

					# Update and display everything
					self.window.blit(self.inventory_background, [0, 0])
					self.window.blit(bandit_text, self.center_text(bandit_text))

					pygame.display.update()

				# Start battle
				bandit_battle = Battle(self, [self.player], bandits)
				battle_result = bandit_battle.start_battle()

				with self.load():
					if battle_result:
						self._bandit_battle_reward(num_of_bandits)
						return "win"
					else:
						self.set_game()
						return "lose"
			else:
				pass

	def _bandit_battle_reward(self, num_of_bandits):
		"""
		Gives a reward to the player if the he won the battle.
		"""

		reward = choice(range(1, 15*num_of_bandits))
		self.player.items["Money"] += reward

		if num_of_bandits == 1:
			won_battle_text = self.display_text("You crushed that bandits!",
												BLACK)
		else:
			won_battle_text = self.display_text("You crushed those bandits!",
												BLACK)

		reward_text = self.display_text("You got {} coins.".format(reward),
										BLACK)

		while True:
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					self.quit_game()

				if event.type == pygame.KEYDOWN:
					return True

			# Display and update everything
			self.window.blit(self.inventory_background, [0, 0])
			self.window.blit(won_battle_text, self.center_text(won_battle_text))
			self.window.blit(reward_text,
							[self.center_text_x(reward_text),
							 self.WINDOW_HEIGHT/1.8])

			pygame.display.update()

		






