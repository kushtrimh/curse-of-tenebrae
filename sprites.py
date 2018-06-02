import sys
import os
from datetime import datetime
from random import choice, randint
import pygame
import solgame
from battle import Skill

class Player(pygame.sprite.Sprite):
	# All the clothes name to be used to wear them
	# and the attributes they increase
	CLOTHES = {
		"cloak": (("strength", 4), ("defense", 4)),
		"band": (("strength", 3), ("defense", 2)),
		"custos": (("strength", 6), ("defense", 5)),
		"custos-caeli": (("strength", 8), ("defense", 6)),
		"draco": (("strength", 15), ("defense", 13)),
		"froz": (("strength", 13), ("defense", 11)),
		"froz-deus": (("strength", 17), ("defense", 15)),
		"ignis-draco": (("strength", 16), ("defense", 14)),
		"miles": (("strength", 10), ("defense", 9)),
		"miles-caeli": (("strength", 11), ("defense", 10)),
		"mortem": (("strength", 20), ("defense", 20)),
		"officer": (("strength", 6), ("defense", 6)),
		"tego": (("strength", 16), ("defense", 15)),
		"teneb": (("strength", 22), ("defense", 22)),
	}

	def __init__(self, game, name, character, x, y, sprite_images, warrior_image=None):
		super(Player, self).__init__()
		# Character
		self.character = character
		self.name = name

		self.game = game

		# Moving Parts
		self.x = x
		self.y = y

		self.world_x = 0
		self.world_y = 0

		self.lead_x = 0
		self.lead_y = 0

		self.speed = 5

		# The player without clothes
		self.normal_clothes = sprite_images

		# Set image, all_images and largest num
		self._load_images(self.normal_clothes)

		# Tells in which kingdom the user was in
		self.kingdom_in = None

		# 'Motion Image' is used for the next image
		# in the animation
		self.direction = "down"
		self.motion_image = 0
		self.change_image = 0
		self.rect = self.image.get_rect()

		self.last_building = None
		self.last_direction = "down"

		self.can_talk_to_npc = None
		self.talking_with_npc = False

		self.sleep_time = datetime.now().minute

		# Clothes
		self.cloth_x = 0
		self.cloth_y = 0
		self.cloth_on = None
		self.equipped_clothes = {}

		# Attributes
		self.experience = 0
		self.level = 1
		self.can_carry = 20
		self.max_health = 100
		self.max_magic = 50
		self.max_stamina = 150

		self.health = 100
		self.magic = 50
		self.stamina = 100
		self.strength = 30
		self.spell_strength = 20
		self.defense = 20
		self.weight = 0
		self.money = 100

		# Items initialization
		self.health_potions = 0
		self.magic_potions = 0
		self.apples = 0

		# Items as dictionaries
		self.items = {
			"Money": self.money,
			"Health Potions": self.health_potions,
			"Magic Potions": self.magic_potions,
			"Apple": self.apples
		}

		self.chest = {}

		### BATTLE SYSTEM ATTRIBUTES
		# Skills
		# All skills is a dictionary of all player skills
		# and skills is the skills he's using
		self.allskills = {}
		self.skills = {}
		self.allowed_skills = {}

		# Add warrior image
		try:
			self.warrior_image = pygame.image.load(warrior_image).convert()
		except (AttributeError, OSError, pygame.error):
			try:
				img_path = os.path.join("battle/warriors", self.character)
				self.warrior_image = pygame.image.load("{}.png".format(img_path))
			except (AttributeError, OSError, pygame.error):
				try:
					img_path = os.path.join("battle/warriors", self.name)
					self.warrior_image = pygame.image.load("{}.png".format(img_path))
				except pygame.error as err:
					self.warrior_image = pygame.Surface((130, 150))
					# print "[!Error Warrior Image] {}".format(err)

		# Set warrior_rect
		try:
			self.warrior_rect = pygame.Rect(0, 
											0, 
											self.warrior_image.get_width(), 
											self.warrior_image.get_height())
		except AttributeError:
			pass

		# Used to display healthbar in battle system
		# (used in HP percentange calculation)
		self.start_health = self.health

		# Those two are used by enemies and allies,
		# to check if an attack skill or defense skill was places
		# on this instance
		self.placed_skills = []
		self.being_defended = False
		# The defense last added to the player
		# This is used to remove the last defense and add a new of
		# If a new one is chosed
		self.last_defense_skill = None
		self.last_defense_turn = 0

		# Attributes that hold the skill the user wants to perform
		# and the warrior on which he wants to perform that skill
		self.chosed_skill = None
		self.chosed_warrior = None

	def _load_images(self, sprite_images):
		"""
		Loads the images of the player
		"""
		## FIX IT ME NPC
		try:
			self.all_images = sprite_images
			self.largest_motion_image = len(self.all_images["down"])

			if sprite_images:
				default = self.all_images["down"][0]
				self.image = default
			else:
				self.image = pygame.Surface((10, 10))
		except TypeError:
			# If an npc doesn't move we give only an image to him
			self.all_images = []
			self.largest_motion_image = 0
			self.image = pygame.image.load(sprite_images).convert_alpha()

		# self.direction = "down"
		# self.motion_image = 0
		# self.change_image = 0
		# self.rect = self.image.get_rect()

	def set_allskills(self, skill_names):
		"""
		Accepts a list of skill names and sets those skills
		to allskills player dictionary
		"""

		for name in skill_names:
			skill = Skill(self.game, self, name)
			self.allskills[name] = skill

	def set_skills(self, skill_names):
		"""
		Accepts a list of skill names and
		sets the skills of the player, adds skills to the
		'skills' dictionary the same way they get added
		on the 'Game.skills' dictionary, except now
		the value its the Skill object.
		"""

		for name in skill_names:
			if name in self.game.skills and len(self.skills) < 4:
				# Add it to skills since it doesn't exist yet
				self.skills[name] = Skill(self.game, self, name)
			elif len(self.skills) >= 4:
				# Add it to all skills since only 4 skills can be used
				# at the same time
				self.allskills[name] = Skill(self, name)
			else:
				print "{}: !Skill Does Not Exist".format(name)

	def set_allowed_skills(self):
		"""
		Checks the skills that the player can perform
		based on the stamina/magic player attributes and
		skill cost
		"""

		for skillname, skill in self.skills.iteritems():
			energytype = skill.entype
			if skill.countdown == 0:
				if energytype == "physical":
					if skill.cost < self.stamina:
						self.allowed_skills[skillname] = skill
					else:
						try:
							del self.allowed_skills[skillname]
						except KeyError:
							pass
				elif energytype == "magic":
					if skill.cost < self.magic:
						self.allowed_skills[skillname] = skill
					else:
						try:
							del self.allowed_skills[skillname]
						except KeyError:
							pass
				else:
					raise Exception("That doesn't exist!")
			else:
				try:
					del self.allowed_skills[skillname]
				except KeyError:
					pass

	def set_clothes(self, cloth_name):
		"""
		Wears the clothes given by the name to the player.
		"""

		if cloth_name != None:
			self.cloth_on = cloth_name

			# Get cloth surfaces
			# - 1 because count start from 1 so instead of 8 it's 9
			player_clothes = solgame.get_images_with_directions(
										"clothes/{}".format(cloth_name),
									     self.largest_motion_image-1)
			
			# Load surfaces
			self._load_images(player_clothes)

			# Get and set attributes
			strength, defense = self.CLOTHES[cloth_name]
			
			self.strength += strength[1]
			self.defense += defense[1]
		else:
			# If cloth_name is 'None' remove clothes
			self._load_images(self.normal_clothes)

	def remove_clothes(self):
		"""
		Sets the clothes of the player to the normal clothes
		he has from the start
		"""

		self._load_images(self.normal_clothes)

		# Get and remove attributes
		strength, defense = self.CLOTHES[self.cloth_on]

		self.strength -= strength[1]
		self.defense -= defense[1]

		self.cloth_on = None

	# Attributes
	def set_name_and_character(self, name, character):
		self.name = name
		self.character = character

	def level_up(self):
		# Level
		self.experience = 0
		self.level += 1

		# Upgrade Attributes
		self.strength += 5
		self.defense += 5
		self.can_carry += 5
		self.max_health += 15
		self.max_magic += 10

		self.money += 25

	# Moving and position
	def set_direction(self):
		"""
		Set's direction of the player so it can be used
		on the next image
		"""

		if self.lead_x == self.speed and self.lead_y == self.speed:
			self.direction = "right"
		elif self.lead_x == -self.speed and self.lead_y == self.speed:
			self.direction = "left"
		elif self.lead_x == self.speed and self.lead_y == -self.speed:
			self.direction = "right"
		elif self.lead_x == -self.speed and self.lead_y == -self.speed:
			self.direction = "left"
		elif self.lead_x == self.speed:
			self.direction = "right"
		elif self.lead_x == -self.speed:
			self.direction = "left"
		elif self.lead_y == self.speed:
			self.direction = "down"
		elif self.lead_y == -self.speed:
			self.direction = "up"
		else:
			self.direction = self.direction

	def set_position(self, x, y):
		"""
		Sets the position of the player in the game window
		to the given x and y
		"""

		self.rect.x = x
		self.rect.y = y

	def set_motion_image(self):
		"""
		Sets the self.image using the current user direction
		(the direction the player is going towards) and using 
		motion_image which contains the index of the image
		to grabed from the list of images in that direction
		"""

		current_direction = self.all_images[self.direction]
		self.image = current_direction[self.motion_image]

	def set_kingdom_in(self, kingdom_name):
		"""
		Sets the kingdom in which the user is in
		using the given kingdom_name
		"""

		self.kingdom_in = kingdom_name

	def calculate_weight(self):
		"""
		Calculates and sets the weight of items the user has,
		if that value is equal to 'can_carry' then he cannot carry,
		more items, until he places some in his inventory
		"""

		weight = 0
		for item in self.items:
			if item == "Health Potions" or item == "Magic Potions":
				weight += self.items[item]

		self.weight = weight

	# Drinking and eating
	def drink_health_potion(self):
		"""
		Drinks one health potion and gains health
		"""

		if self.health >= self.max_health:
			return False
		else:
			self.health += 15
			self.items["Health Potions"] -= 1

		if self.health >= self.max_health:
			self.health = self.max_health

		# Calculate weight
		self.calculate_weight()

	def drink_magic_potion(self):
		"""
		Drinks a magic potion and gains magic
		"""

		if self.magic >= self.max_magic:
			return False
		else:
			self.magic += 15
			self.items["Magic Potions"] -= 1

		if self.magic >= self.max_magic:
			self.magic = self.max_magic

		# Calculate weight
		self.calculate_weight()

	# Buildings and shops
	def set_last_building(self, building):
		self.last_building = building

	def set_position_by_last_building(self):
		self.rect.x = self.last_building.rect.x
		self.rect.y = self.last_building.rect.y + 50

	def buy(self, shop, article, clothes=False):
		"""
		Buys something from the shop

		If something was bought it returns a Surface message
		telling that it was bought, if it was not and there
		was a problem then it returns the problem
		"""
		
		if clothes:
			article = article.lower()

		# Get index of the article from the shop articles
		article_index = shop.articles.index(article)

		# Get cost
		article_cost = shop.articles_cost[article_index]
		
		# Buy it xD
		if article in self.equipped_clothes:
			return "You already have this costume."

		if self.weight >= self.can_carry:
			return "You cannot carry more items."
		elif self.items["Money"] < article_cost:
			return "You don't have enough money."
		else:
			self.items["Money"] -= article_cost

		if clothes:
			# Check if those are clothes because the buying process
			# is different
			self.equipped_clothes[article] = "Owns"
		else:
			##!! The change we make for potions to correspond with
			# player items, since we don't include the 'potion' in the images.
			# The list down below contains all the name which are 'potions'
			if article in ["Health", "Magic"]:
				article = "{} Potions".format(article)

			# Add the article to player 'stats/inventory'
			self.items[article] += 1

			# Calculate weight
			self.calculate_weight()

			return "{} bought!".format(article)

	def sell(self, shop, article):
		"""
		Sells the chose article, the money you get is the half of
		the price of that item
		"""

		article_cut = article.split(" ")[0]

		# Get index of article from the shop
		article_index = shop.articles.index(article_cut)

		# Get money of the item we're going to sell
		article_value = shop.articles_cost[article_index]/2

		# Get count
		article_count = self.items[article]

		if article_count <= 0:
			return "You cannot sell something you don't have."
		else:
			self.items["Money"] += article_value
			self.items[article] -= 1

		# Calculate weight
		self.calculate_weight()

		return "{} sold!".format(article)

	def sell_clothes(self, shop, cloth):
		"""
		Sells the clothes that the player has
		"""

		cloth = cloth.lower()

		# Get index of article from the shop
		cloth_index = shop.articles.index(cloth)

		# Get money of the item we're going to sell
		cloth_value = shop.articles_cost[cloth_index]/2

		if cloth in self.equipped_clothes:
			self.items["Money"] += cloth_value
			self.equipped_clothes.pop(cloth)

			# If user is wearing that cloth remove it
			if self.cloth_on == cloth:
				self.cloth_on = None
				self._load_images(self.normal_clothes)
		else:
			return "You cannot sell something you don't have."

		# Calculate weight
		self.calculate_weight()

		return "{} sold!".format(cloth)



	def update(self, objects_group, is_player=True):
		"""
		objects_group contains sprite groups of the objects from the tmx data
		first is blocks_group
		second is buildings_group
		third is npc_group
		"""
		self.rect.x += self.lead_x

		# Objects group [0] it's the blocks_group
		#COLLISION.. look at this
		blocks = pygame.sprite.spritecollide(self, objects_group[0], False)
		for block in blocks:
			#####Ndrroj left or right to have an effect of teleport xD
			# Means we're going right
			if self.lead_x > 0:
				self.rect.right = block.rect.left
			# Means we're going left
			elif self.lead_x < 0:
				self.rect.left = block.rect.right

		self.rect.y += self.lead_y

		blocks = pygame.sprite.spritecollide(self, objects_group[0], False)
		for block in blocks:
			# Means we're going down
			if self.lead_y > 0:
				self.rect.bottom = block.rect.top
			#Means we're going up
			elif self.lead_y < 0:
				self.rect.top = block.rect.bottom

		#MOVING.. look at this
		# If direction is the same as the last one, continue animation
		# Else set the animation to start from the beggining in the new direction
		if self.direction == self.last_direction:

			# THE CHANGE WE MADE ME CHANGE_IMAGE MA KADAL
			self.change_image += 0.5
			if self.change_image == 1:
				self.change_image = 0
				# Add one to motion image so the next image
				# of the same direction is used for the animation
				self.motion_image += 1
		else:
			# Sets the last_direction to the new direction
			# and since direction changed set motion_image to 0
			# so we start from the beggining with the animation
			self.last_direction = self.direction
			self.motion_image = 0

		# If the current image is the last of the animation
		# start the animation from the beggining
		if self.motion_image == self.largest_motion_image:
			self.motion_image = 0

		# If player is not moving, set the image to 'standing'
		# which is the beggining
		if self.lead_x == 0 and self.lead_y == 0:
			self.motion_image = 0

		# Set the image
		self.set_motion_image()

		# Clothes
		self.cloth_x = self.rect.x
		self.cloth_y = self.rect.y

		###NPC
		# The area in which the player is able to talk with NPC
		npc_talk_area = 50

		# Since NPC derives from the player,
		# check if the player is calling this
		# since it should be used only the the player
		# not by the NPC themselves
		if is_player:
			# Set this to None everytime the function runs
			# so if one of the npc is in the range in which we can talk
			# this variable will hold that 'NPC', if npc not in the range,
			# this remains None
			self.can_talk_to_npc = None

			for npc in objects_group[2]:
				if (self.rect.x >= npc.rect.x - npc_talk_area and 
					self.rect.x <= npc.rect.x + npc.rect.width + npc_talk_area and 
					self.rect.y >= npc.rect.y - npc_talk_area and 
					self.rect.y <= npc.rect.y + npc.rect.height + npc_talk_area):
					# Press space to talk to npc
					self.can_talk_to_npc = npc

			# Check collision with npc
			npc_collisions = pygame.sprite.spritecollide(self, objects_group[2], False)
			for npc in npc_collisions:
				if self.lead_x > 0:
					self.rect.right = npc.rect.left
				elif self.lead_x < 0:
					self.rect.left = npc.rect.right

			npc_collisions = pygame.sprite.spritecollide(self, objects_group[2], False)
			for npc in npc_collisions:
				if self.lead_y > 0:
					self.rect.bottom = npc.rect.top
				elif self.lead_y < 0:
					self.rect.top = npc.rect.bottom

class World(pygame.sprite.Sprite):
	def __init__(self, world_background, window, world_objects, world_buildings, npc_group, player):
		super(World, self).__init__()

		self.world_objects = world_objects
		self.world_buildings = world_buildings

		self.npc_group = npc_group

		self.image = pygame.image.load(world_background).convert()

		self.rect = self.image.get_rect()

		self.player = player
		self.window = window

		self.WINDOW_HEIGHT = self.window.get_height()
		self.WINDOW_WIDTH = self.window.get_width()

		self.func = None

	def update(self, change_x, change_y, npc_group):
		# Scrolling the world and everything in it!
		self.player.lead_x = change_x
		self.player.lead_y = change_y

		world_x_scrolling = False
		y_scrolling = False

		# X
		if self.player.rect.x >= self.WINDOW_WIDTH - self.WINDOW_WIDTH/4 and self.player.lead_x > 0:
			if not self.rect.x <= -self.rect.width + self.WINDOW_WIDTH:
				# If player is not at the end of the window
				self.rect.x -= change_x
				self.player.rect.x -= change_x
				world_x_scrolling = True
			else:
				# If player is at the end of the window
				self.player.rect.x -= 0
		elif self.player.rect.x <= self.WINDOW_WIDTH/4 and self.player.lead_x < 0:
			if not self.rect.x >= 0:
				self.rect.x -= change_x
				self.player.rect.x -= change_x
				world_x_scrolling = True
			else:
				self.player.rect.x -= 0
		# Y
		if self.player.rect.y >= self.WINDOW_HEIGHT - self.WINDOW_HEIGHT/4 and self.player.lead_y > 0:
			if not self.rect.y <= -self.rect.height + self.WINDOW_HEIGHT:
				self.rect.y -= change_y
				self.player.rect.y -= change_y
				y_scrolling = True
			else:
				self.rect.y -= 0
		elif self.player.rect.y <= self.WINDOW_HEIGHT/4 and self.player.lead_y < 0:
			if not self.rect.y >= 0:
				self.rect.y -= change_y
				self.player.rect.y -= change_y
				y_scrolling = True
			else:
				self.player.rect.y -= 0

		# Collision per borders
		if self.player.rect.x >= self.WINDOW_WIDTH - self.player.rect.width and self.player.lead_x > 0:
			self.player.rect.x -= self.player.speed
		elif self.player.rect.x <= 0 and self.player.lead_x < 0:
			self.player.rect.x += self.player.speed

		if self.player.rect.y >= self.WINDOW_HEIGHT - self.player.rect.height and self.player.lead_y > 0:
			self.player.rect.y -= self.player.speed
		elif self.player.rect.y <= 0 and self.player.lead_y < 0:
			self.player.rect.y += self.player.speed


		# Player map division
		self.player.world_x = abs(self.rect.x)
		self.player.world_y = abs(self.rect.y)

		# Npc collision
		for npc in npc_group:
			if world_x_scrolling:
				npc.rect.x -= change_x
				npc.room.x -= change_x
			if y_scrolling:
				npc.rect.y -= change_y
				npc.room.y -= change_y

		# Nese ja bojm te te dyjat me ndrru edhe x edhe y, at'her edhe pse osht tu livrit
		# psh me y ama screen sosht tu u sill, at'her ka efekt n'object kshtuqe ashtu osht gabim
		for obj in self.world_objects:
			if world_x_scrolling:
				obj.rect.x -= change_x
			if y_scrolling:
				obj.rect.y -= change_y

		for obj in self.world_buildings:
			if world_x_scrolling:
				obj.rect.x -= change_x
			if y_scrolling:
				obj.rect.y -= change_y

class NPC(Player):
	def __init__(self, game, name, x, y, images, moves=True, can_chat=False, warrior_image=None):
		super(NPC, self).__init__(game, name, None, 50, 50, images, warrior_image)

		# Room is the place in which the NPC can walk
		self.room = pygame.Rect(x, y, 70, 70)
		self.room_center = self.room.center

		self.speed = 2
		self.speed_moves = [-2, 2, 0]

		self.lead_x = 0
		self.lead_y = 0

		self.can_chat = can_chat

		self.moves = moves

		# If it's movable then we don't need those
		if self.moves:
			self.all_images = images
			self.largest_motion_image = len(self.all_images["down"])

			if images:
				default = self.all_images["down"][0]
				self.image = default
			else:
				self.image = pygame.Surface((10, 10))
		else: 
			self.image = pygame.image.load(images).convert_alpha()

		# 'Motion Image' is used for the next image
		# in the animation
		self.direction = "down"
		self.motion_image = 0
		self.change_image = 0
		self.rect = self.image.get_rect()

		self.rect.x = x
		self.rect.y = y

		# Interactions
		self.talks = []
		self.questions = []
		self.answers = []

		# Set the position of NPC
		self.set_position()

		self.talking = False

		# Brain, this is used in the battle system
		# it's the AI of the game
		self.brain = None

	def generate_x(self):
		self.lead_x = choice(self.speed_moves)

	def generate_y(self):
		self.lead_y = choice(self.speed_moves)

	def set_answers(self, answers):
		if answers is not None:
			self.answers = answers
		else:
			self.answers = []

	def set_attributes(self, health=0, magic=0, stamina=0, 
					  max_health=0, max_magic=0, max_stamina=0,
					  strength=0, defense=0, spell_strength=0):
		self.health = health
		self.magic = magic
		self.stamina = stamina
		self.max_magic = max_magic
		self.max_health = max_health
		self.max_stamina = max_stamina
		self.strength = strength
		self.defense = defense
		self.spell_strength = spell_strength

	def set_position(self):
		self.rect.x = self.room.centerx
		self.rect.y = self.room.centery

	def set_talks(self, talks):
		self.talks = talks

	def set_questions(self, questions):
		self.questions = questions

	def update_npc(self, blocks_group, player_group, npc_group):
		if not self.talking and self.moves:
			# If it's not talking then move
			if self.lead_x == 0 and self.lead_y == 0:
				self.generate_x()
				self.generate_y()
			self.update([[], [], blocks_group], False)

			# Collision with room
			if self.rect.x <= self.room.x and self.lead_x < 0:
				self.lead_x = 2
			elif self.rect.x >= self.room.right and self.lead_x > 0:
				self.lead_x = -2
			if self.rect.y <= self.room.y and self.lead_y < 0:
				self.lead_y = 2
			elif self.rect.y >= self.room.bottom and self.lead_y > 0:
				self.lead_y = -2
			
			should_move = randint(0, 100)
			if should_move > 45 and should_move < 50:
				check = choice(["x", "y"])
				if check == "y":
					self.lead_y = choice(self.speed_moves)
				elif check == "x":
					self.lead_x = choice(self.speed_moves)

			# NPC collision with blocks
			# For X
			# Add it
			self.rect.x += self.lead_x
			#.

			collided_block = pygame.sprite.spritecollide(self, blocks_group, False)
			for block in collided_block:
				if self.lead_x > 0:
					self.rect.right = block.rect.left
				elif self.lead_x < 0:
					self.rect.left = block.rect.right

			# Remove it
			self.rect.x -= self.lead_x
			#,

			# For Y
			# Add it
			self.rect.y += self.lead_y
			#. 

			collided_block = pygame.sprite.spritecollide(self, blocks_group, False)
			for block in collided_block:
				if self.lead_y > 0:
					self.rect.bottom = block.rect.top
				elif self.lead_y < 0:
					self.rect.top = block.rect.bottom

			# Remove it
			self.rect.y -= self.lead_y
			#.

			# NPC collision with player
			collided_with_player = pygame.sprite.spritecollideany(self, player_group)
			if collided_with_player:
				if self.lead_x > 0:
					self.rect.right = collided_with_player.rect.left
				elif self.lead_x < 0:
					self.rect.left = collided_with_player.rect.right
			collided_with_player = pygame.sprite.spritecollideany(self, player_group)
			if collided_with_player:
				if self.lead_y > 0:
					self.rect.bottom = collided_with_player.rect.top
				elif self.lead_y < 0:
					self.rect.top = collided_with_player.rect.bottom



		else:
			# If it's talking set motion image to 0
			self.motion_image = 0

class Map(pygame.sprite.Sprite):
	def __init__(self, window, background, player_x, player_y):
		super(Map, self).__init__()

		self.window = window
		self.WINDOW_WIDTH = self.window.get_width()
		self.WINDOW_HEIGHT = self.window.get_height()

		self.image = pygame.image.load(background).convert()
		
		self.rect = self.image.get_rect()

		self.castle_coordinates = []

	def map_borders(self, map_blocks):
		pass

	def update(self, mplayer, change_x, change_y, map_blocks, kingdom_blocks, story_rect):
		mplayer_rect = mplayer.rect

		mplayer.lead_x = change_x
		mplayer.lead_y = change_y

		x_scrolling = False
		y_scrolling = False

		# X
		if mplayer_rect.x >= self.WINDOW_WIDTH - self.WINDOW_WIDTH/4 and mplayer.lead_x > 0:
			if not self.rect.x <= -self.rect.width + self.WINDOW_WIDTH:
				self.rect.x -= change_x
				mplayer_rect.x -= change_x
				x_scrolling = True
			else:
				mplayer_rect.x -= 0
		elif mplayer_rect.x <= self.WINDOW_WIDTH/4 and mplayer.lead_x < 0:
			if not self.rect.x >= 0:
				self.rect.x -= change_x
				mplayer_rect.x -= change_x
				x_scrolling = True
			else:
				mplayer_rect.x -= 0
		# Y
		if mplayer_rect.y >= self.WINDOW_HEIGHT - self.WINDOW_HEIGHT/4 and mplayer.lead_y > 0:
			if not self.rect.y <= -self.rect.height + self.WINDOW_HEIGHT:
				self.rect.y -= change_y
				mplayer_rect.y -= change_y
				y_scrolling = True
			else:
				self.rect.y -= 0
		elif mplayer_rect.y <= self.WINDOW_HEIGHT/4 and mplayer.lead_y < 0:
			if not self.rect.y >= 0:
				self.rect.y -= change_y
				mplayer_rect.y -= change_y
				y_scrolling = True
			else:
				mplayer_rect.y -= 0

		# Collision per borders
		if mplayer_rect.x >= self.WINDOW_WIDTH - mplayer_rect.width and mplayer.lead_x > 0:
			mplayer_rect.x -= mplayer.speed
		elif mplayer_rect.x <= 0 and mplayer.lead_x < 0:
			mplayer_rect.x += mplayer.speed

		if mplayer_rect.y >= self.WINDOW_HEIGHT - mplayer_rect.height and mplayer.lead_y > 0:
			mplayer_rect.y -= mplayer.speed
		elif mplayer_rect.y <= 0 and mplayer.lead_y < 0:
			mplayer_rect.y += mplayer.speed

		# Move objects
		# psh me y ama screen sosht tu u sill, at'her ka efekt n'object kshtuqe ashtu osht gabim
		for obj in map_blocks:
			if x_scrolling:
				obj.rect.x -= change_x
			if y_scrolling:
				obj.rect.y -= change_y

		if story_rect is not None:
			if x_scrolling:
				story_rect.x -= change_x
			if y_scrolling:
				story_rect.y -= change_y

		for obj in kingdom_blocks:
			if x_scrolling:
				obj.rect.x -= change_x
			if y_scrolling:
				obj.rect.y -= change_y

class Blocks(pygame.sprite.Sprite):
	def __init__(self, block_rect, name):
		super(Blocks, self).__init__()

		self.name = name

		x, y, width, height = block_rect
		self.rect = pygame.Rect(x, y, width, height)

class Buildings(pygame.sprite.Sprite):
	def __init__(self, rect, name):
		super(Buildings, self).__init__()

		self.BUILDINGS_PATH = "buildings"

		self.PATH = os.path.join(self.BUILDINGS_PATH, name)

		self.name = name

		self.shop = None

		self.cloth_shop = False
 
		x, y, width, height = rect
		self.rect = pygame.Rect(x, y, width, height)

	def set_shop(self, shop):
		self.shop = shop

class Shops(pygame.sprite.Sprite):
	def __init__(self, building):
		super(Shops, self).__init__()

		self.building = building

		self.name = building.name

		self.articles = []
		self.articles_description = []
		self.articles_cost = []

	def set_articles(self, articles_data):
		"""
		'articles' a tuple containing 3 elements,
		first is the articles name, second the articles info,
		and the last one is the articles articles cost
		"""
		
		for name, description, cost in articles_data:
			if self.building.cloth_shop:
				self.articles.append(name.lower())
			else:
				self.articles.append(name)
			self.articles_description.append(description)
			self.articles_cost.append(cost)