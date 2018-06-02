# This is where battle happens xD
import os
import time
import pygame
from ai import NPCBrain
from colors import *

pygame.font.init()

class Skill(pygame.sprite.Sprite):
	"""
	A class that is used to create skills
	that'll be used both in 'world'(for displaying) and in 'battle'
	"""
	def __init__(self, game, warrior, name):
		"""
		Warrior is the a Player or NPC object that uses
		the skill
		"""
		super(Skill, self).__init__()

		self.game = game
		# Set warrior
		self.warrior = warrior

		# Skill images path
		self.images_path = "battle/skills"

		try:
			skill_attrs = game.skills[name]
		except KeyError as err:
			print "[ !Error ]{} is yet to be created!".format(str(err))
			game.quit_game()

		# Set attributes
		try:
			self.image = pygame.image.load(skill_attrs[1]).convert_alpha()
		except pygame.error:
			self.image = pygame.image.load(
								os.path.join(self.images_path, skill_attrs[1])
								).convert()
		self.name = skill_attrs[0]
		self.skilltype = skill_attrs[2]
		self.entype = skill_attrs[3]
		self.dmgdef = skill_attrs[4]
		self.description = skill_attrs[5]
		self.cost = skill_attrs[6]
		self.range = skill_attrs[8]

		self.countdown_constant = skill_attrs[7]
		self.countdown = 0

		# Set rect
		self.rect = self.image.get_rect()

class Battle(object):

	PATH = "battle"
	background = pygame.image.load(
					os.path.join(PATH, "images/warrior.jpg"))
	attributes_font = pygame.font.Font("fonts/ringbearer/ringbearer.ttf", 15)

	def __init__(self, game, warriors, enemy_warriors):

		# Start loading data
		with game.load():

			self.turn = 0
			self.defensive_skills_turns = 3

			self.won = None

			# Warriors is a list of warriors that will be on the team with player
			# Emeny warriors is the other one
			self.warriors = list(warriors)
			self.enemy_warriors = list(enemy_warriors)

			# Warriors that are dead
			# This is used for displaying the skull image
			# On dead warriors
			self.dead = []

			# Check if any of the warriors or enemies are without skills
			self.check_for_skills()

			# Set game
			self.game = game
			self.window = self.game.window

			self.warriors_path = os.path.join(Battle.PATH, "warriors")

			# The warrior we're currently playing with
			# (the clicked warrior)
			self.current_warrior = None

			# Selected warrior is different from chosed warrior
			# because clicked warrior is only used to hold the warrior
			# for which info will
			self.selected_warrior = None
			self.selected_skill = None
			self.clicked_last = None

			# Checks if there was a turn, to display turn info
			self.turn_made = False

			# # Play music
			# pygame.mixer.music.load(
			# 		os.path.join(Battle.PATH, "music/skyworld.mp3"))
			# # pygame.mixer.music.play(-1)

			# Shifts
			self.wshift_x = self.game.WINDOW_WIDTH/1.22
			self.wshift_y = 115
			self.wshift_by = 150

			self.ewshift_x = 15
			self.ewshift_y = 115

		 	# Get length of warriors
			warriors_count = len(self.warriors)
			
			# Check if its one warrior to change position of
			# warrior image
			if warriors_count == 1:
				self.wshift_y = self.game.WINDOW_HEIGHT/4
			elif warriors_count == 2:
				self.wshift_y = self.game.WINDOW_HEIGHT/5.5

		 	# Get length of enemy warriors
			ewarriors_count = len(self.enemy_warriors)

			if ewarriors_count == 1:
				self.ewshift_y = self.game.WINDOW_HEIGHT/4
			elif ewarriors_count == 2:
				self.ewshift_y = self.game.WINDOW_HEIGHT/5.5

			# Skill shifts
			self.skill_shift_x = self.game.WINDOW_WIDTH/1.4
			self.skill_shift_y = self.wshift_y+25
		 	self.skill_shift_by = -90

		 	# Healthbar shift and width
		 	self.healthbar_shift_y = 15
		 	self.hpbar_width = self.warriors[0].warrior_rect.width

			# Images
			self.skillscroll_bg = pygame.image.load("images/skillscroll.png").convert_alpha()
			self.warrior_glowing = pygame.image.load("images/warriorselector.png").convert_alpha()
			self.turn_info_bg = pygame.image.load("images/turninfoscroll.png").convert_alpha()
			self.skull_img = pygame.image.load("images/skull.png").convert_alpha()
			self.not_allowed_glowing = pygame.image.load("images/notallowedselector.png").convert_alpha()
			self.alpha_black_screen = pygame.image.load("images/alphablackscreen.png").convert_alpha()
			self.shield_img = pygame.image.load("images/shield.png").convert_alpha()

			self.turn_info_btn = pygame.image.load("images/turninfo.png").convert_alpha()
			self.turn_info_btn_rect = pygame.Rect(25, 
												 self.game.WINDOW_HEIGHT-75, 
												 self.turn_info_bg.get_width(), 
												 self.turn_info_bg.get_height())

			self.skill_glowing_attck = pygame.image.load("images/skillselectorattack.png").convert_alpha()
			self.skill_glowing_def = pygame.image.load("images/skillselectordefense.png").convert_alpha()
			self.skill_glowing_reg = pygame.image.load("images/skillselectorregen.png").convert_alpha()

			# Texts
			self.waiting_for_enemy = self.game.display_text("Waiting for enemy...", BLACK)


			# Set skill rects
			for ally in self.warriors:
				self.game.set_sprite_rects(ally.skills, 
										   self.skill_shift_x,
										   self.skill_shift_y,
										   self.skill_shift_by,
										   dictionary=True)
				self.skill_shift_y += 150

			# Set ally rects
			self.set_warrior_image_rect(self.warriors,
										self.wshift_x,
										self.wshift_y,
										0,
										self.wshift_by + self.healthbar_shift_y)

			# Set enemy rects
			self.set_warrior_image_rect(self.enemy_warriors, 
										self.ewshift_x,
										self.ewshift_y,
										0,
										self.wshift_by + self.healthbar_shift_y)

			# Time used when a turn happens
			# Default is 5 seconds
			self.next_turn_delay = 1

			# Get needed y for display skills info and warrior info
			self.heighty = self.skillscroll_bg.get_height()/4

			# A list containing the info
			self.turn_info = []

			# Regenerations
			self.stamina_regeneration = 7
			self.magic_regeneration = 5
			self.health_regeneration = 5

			# Set NPC Brain
			self.set_npc_brains()

			self.set_start_health()
			
	def set_warrior_image_rect(self, warriors, x, y, shift_x, shift_y, dictionary=False):
		"""
		Set rects of warrior images.
		! Inspired by set_sprite_rects of Game Class xD
		"""		

		if not dictionary:
			for sprt in warriors:
				# Set points
				sprt.warrior_rect.x = x
				sprt.warrior_rect.y = y
				# Shift
				x += shift_x
				y += shift_y
		else:
			for sprt in sprites:
				sprite = sprites[sprt]
				# Set points
				sprite.warrior_rect.x = x
				sprite.warrior_rect.y = y
				# Shift
				x += shift_x
				y += shift_y

	def regenerate(self):
		"""
		Regenerates health, stamina and magic
		for all warriors and enemy warriors
		"""
		def calculate_reg(attr, attr_max, attr_reg):
			attr_sub = attr_max - attr
			if attr >= attr_max:
				attr_result = 0
			elif attr_sub <= attr_reg:
				attr_result = attr_sub
			else:
				attr_result = attr_reg

			return attr_result

		for warrior in self.warriors + self.enemy_warriors:
			warrior.health += calculate_reg(warrior.health, 
											warrior.max_health, 
											self.health_regeneration)
			warrior.stamina += calculate_reg(warrior.stamina, 
										     warrior.max_stamina, 
										     self.stamina_regeneration)
			warrior.magic += calculate_reg(warrior.magic,
										   warrior.max_magic,
										   self.magic_regeneration)

	def clicked_warrior(self, warrior):
		"""
		Returns True if a warrior image was clicked, False otherwise,
		inspired by Game class clicked_surface xD
		"""

		mpressed = pygame.mouse.get_pressed()
		mposition = pygame.mouse.get_pos()

		if mpressed[0] == 1:
			clicked = warrior.warrior_rect.collidepoint(mposition)
			if clicked:
				return True

		return False

	def check_for_skills(self):
		"""
		Checks if any of the warriors or enemies are without skills,
		and if they are, we assign some to them.
		"""
		i = 0

		for warrior in self.warriors + self.enemy_warriors:
			if len(warrior.skills) == 0:
				for skillname, skill in warrior.allskills.iteritems():
					warrior.skills[skillname] = skill

					if i == 4:
						i = 0
						break

					i += 1

	def clear_placed_skills(self):
		"""
		Clears placed skills of player, allies and enemies,
		and clears all selectros of all warriors, selectors are
		chosed_skill and chosed_warrior.
		"""

		for enemy in self.enemy_warriors:
			enemy.placed_skills = []

		for ally in self.warriors:
			ally.placed_skills = []

	def clear_warriors_selectors(self):
		for warrior in self.warriors:
			warrior.chosed_warrior = None
			warrior.chosed_skill = None

	def set_start_health(self):
		for warrior in self.warriors + self.enemy_warriors:
			warrior.start_health = warrior.health

	def descrease_skills_countdown(self):
		"""
		Decreases the countdown of everyskill by -1.
		"""
		for warrior in self.warriors + self.enemy_warriors:
			for skill in warrior.skills.itervalues():
				if skill.countdown != 0:
					skill.countdown -= 1


	def set_npc_brains(self):
		"""
		Create brain instances from the NPCBrain class
		for every enemy
		"""

		for npc in self.enemy_warriors:		
			# Create brain
			brain = NPCBrain(self, npc, self.enemy_warriors, self.warriors)
			npc.brain = brain

	def check_for_dead(self):
		"""
		Checks if theres a warrior with health below 0
		to remove him from the game.
		"""

		for warrior in self.warriors:
			if warrior.health <= 0:
				self.warriors.remove(warrior)
				self.dead.append(warrior)

		for enemy in self.enemy_warriors:
			if enemy.health <= 0:
				self.enemy_warriors.remove(enemy)
				self.dead.append(enemy)

	def check_for_winning(self):
		"""
		Checks if all warriors of any sides are all dead
		so the battle is over.
		"""

		battle_over = False
		if len(self.warriors) == 0:
			battle_over = True
			self.won = False
			battle_result = self.game.display_text("Defeated!", SILVER, font_size="big")
		elif len(self.enemy_warriors) == 0:
			battle_over = True
			self.won = True
			battle_result = self.game.display_text("Victory!", SILVER, font_size="big")

		def draw_battle_result():
			self.window.blit(self.alpha_black_screen, [0, 0])
			self.window.blit(self.shield_img,
							self.game.center_text(self.shield_img))
			self.window.blit(battle_result,
							self.game.center_text(battle_result))

		# Decorator
		draw_battle_result = self.game.display_for_time(draw_battle_result, 0)

		if battle_over:
			draw_battle_result()
			return True
		else:
			return False


	def defense_skills_turns_left(self):
		"""
		Counts down the turns of the warriors defense skills(if have any)
		and check if the turn of that skill is 0 to remove it
		"""

		for warrior in self.warriors + self.enemy_warriors:
			if warrior.last_defense_turn > 0:
				warrior.last_defense_turn -= 1
				if warrior.last_defense_turn == 0:
					warrior.defense -= warrior.last_defense_skill.dmgdef
					warrior.last_defense_skill = None
					warrior.being_defended = False

	# def draw_attributes(self):
	# 	"""
	# 	Draws the player attributes on top of the window
	# 	"""
	# 	# Shifting
	# 	shift_y = 10
	# 	# Text and attr shifts
	# 	text_shift_x = self.game.WINDOW_WIDTH/3
	# 	shift_x_by = 75
	# 	# Attr shift x
	# 	attr_shift_x = text_shift_x

	# 	# Player
	# 	player = None

	# 	# Get text for attributes
	# 	health_text = self.game.display_text("Health", WHITE, font_size="small")
	# 	magic_text = self.game.display_text("Magic", WHITE, font_size="small")
	# 	strength_text = self.game.display_text("Strength", WHITE, font_size="small")
	# 	defense_text = self.game.display_text("Defense", WHITE, font_size="small")
	# 	attr_texts = [health_text, magic_text, strength_text, defense_text]

	# 	# Get attributes surfaces
	# 	name = self.game.display_text(player.name, WHITE)
	# 	health = self.game.display_text(str(player.health), WHITE, font_size="small")
	# 	magic = self.game.display_text(str(player.magic), WHITE, font_size="small")
	# 	strength = self.game.display_text(str(player.strength), WHITE, font_size="small")
	# 	defense = self.game.display_text(str(player.defense), WHITE, font_size="small")
	# 	attrs = [health, magic, strength, defense]

	# 	# Draw name
	# 	self.window.blit(name, 
	# 					[self.game.center_text_x(name),
	# 					shift_y])
	# 	# Draw texts
	# 	for attrtext in attr_texts:
	# 		self.window.blit(attrtext, [text_shift_x, shift_y*5])
	# 		text_shift_x += shift_x_by
	# 	# Draw attrs
	# 	for attr in attrs:
	# 		self.window.blit(attr, [attr_shift_x, shift_y*7])
	# 		attr_shift_x += shift_x_by

	def glowing_effect(self, selector_type):
		"""
		OLDSCHOOL SHIT!

		Returns a glowing on skills or player, according to the 'type'
		parameter given to the method
		"""
		selector_path = os.path.join(Battle.PATH, "images/selectors")

		selector_images = []

		for selector in range(self.selectors_num):
			selector_name = "{}{}.png".format(selector_type, selector)
			fullpath = os.path.join(selector_path, selector_name)
			selector_surface = pygame.image.load(fullpath)
			selector_images.append(selector_surface)

		return selector_images

	def draw_warriors(self):
		"""
		Draws warriors on the right side of the window.
		"""

		# Draw warriors
		shift_y = self.wshift_y
		for warrior in self.warriors:
			self.window.blit(warrior.warrior_image, 
							[warrior.warrior_rect.x, 
							 warrior.warrior_rect.y])
			shift_y += self.wshift_by

			# Check if clicked any enemy warrior
			clicked = self.clicked_warrior(warrior)
			# If it was clicked and user chosed a skill
			# set this enemy as 'chosed enemy' which player can attack
			# this turn
			if clicked:
				self.clicked_last = "warrior"
				self.selected_warrior = warrior
				# If the current warrior chosed a skill but not a warrior
				# Set this warrior as his ally to defenend
				try:
					if (self.current_warrior.chosed_skill and 
						self.current_warrior.chosed_skill.skilltype == "defense" and 
						self.current_warrior.chosed_warrior is None):
						# Check for range
						if self.current_warrior.chosed_skill.range == "single":
							# Set chosed warrior
							self.current_warrior.chosed_warrior = warrior
						elif self.current_warrior.chosed_skill.range == "all":
							self.current_warrior.chosed_warrior = self.warriors
					elif (self.current_warrior.chosed_skill and
						  self.current_warrior.chosed_skill.skilltype == "regen" and
						  self.current_warrior.chosed_warrior is None):
						# Check for range
						if self.current_warrior.chosed_skill.range == "single":
							self.current_warrior.chosed_warrior = warrior
						elif self.current_warrior.chosed_skill.range == "all":
							self.current_warrior.chosed_warrior = self.warriors
					else:
						self.current_warrior = warrior
				except AttributeError:
					self.current_warrior = warrior

	def draw_enemy_warriors(self):
		"""
		Draws enemy warrios on the left side of the window.
		"""

		# Draw enemy warriors
		shift_y = self.ewshift_y
		for ewarrior in self.enemy_warriors:
			# self.window.blit(ewarrior.warrior_image, [self.ewshift_x, shift_y])
			# shift_y += self.wshift_by
			self.window.blit(ewarrior.warrior_image, 
							[ewarrior.warrior_rect.x, 
							ewarrior.warrior_rect.y])

			# Check if clicked any enemy warrior
			clicked = self.clicked_warrior(ewarrior)
			# If it was clicked and user chosed a skill
			# set this enemy as 'chosed enemy' which player can attack
			# this turn

			if clicked:
				self.clicked_last = "warrior"
				self.selected_warrior = ewarrior
				# If a skill is chosed and skills its an
				# attack type skill chose this enemy to attack
				try:
					if self.current_warrior.chosed_skill and self.current_warrior.chosed_skill.skilltype == "attack":
						if self.current_warrior.chosed_skill.range == "single":
							self.current_warrior.chosed_warrior = ewarrior
						elif self.current_warrior.chosed_skill.range == "all":
							self.current_warrior.chosed_warrior = self.enemy_warriors
				except AttributeError:
					pass

	def draw_skills(self):
		"""
		Draw player skills according to the player position
		"""

		# Set allowed skills
		for warrior in self.warriors:
			warrior.set_allowed_skills()

		# Draw skills
		# shift_x = self.skill_shift_x

		for warrior in self.warriors:
			for skillname in warrior.skills:
				skill = warrior.skills[skillname]
				self.window.blit(skill.image, [skill.rect.x, skill.rect.y])
				# Check if cliks skill
				clicked = self.game.clicked_surface(skill)
				if clicked:
					self.clicked_last = "skill"
					self.selected_skill = skill
					
					try:
						# Set current warrior
						self.current_warrior = skill.warrior
						if skillname in warrior.allowed_skills:
							# If a new skill was clicked and user has a chosed warrior
							# clear the chosed warrior of the current warrior
							if self.current_warrior.chosed_warrior:
								self.current_warrior.chosed_warrior = None
								self.current_warrior.chosed_skill = skill
							else:
								self.current_warrior.chosed_skill = skill
						else:
							# On a selected not allowed skill put chosed skill and warrior to None
							self.current_warrior.chosed_skill = None
							self.current_warrior.chosed_warrior = None
					except AttributeError:
						pass

	def draw_skill_info(self):
		"""
		Displays about a skill at top of the window
		if that skills is clicked.
		"""

		# Draw background
		self.window.blit(self.skillscroll_bg, [0, 0])

		# Get skill info
		name = self.game.display_text(self.selected_skill.name, BLACK, font_size="small")
		dmgtype = self.game.display_text(self.selected_skill.skilltype, BLACK, font_size="small")
		entype = self.game.display_text(self.selected_skill.entype, BLACK, font_size="small")
		dmgdef = self.game.display_text(str(self.selected_skill.dmgdef), BLACK, font_size="small")
		description = self.game.display_text(self.selected_skill.description, BLACK, font_size="small")
		cost = self.game.display_text("Cost {}".format(self.selected_skill.cost), BLACK, font_size="small")
		skillrange = self.game.display_text(str(self.selected_skill.range), BLACK, font_size="small")

		# Draw skill info
		self.window.blit(name, [100, self.heighty])
		self.window.blit(skillrange, [325, self.heighty])
		self.window.blit(dmgtype, [400, self.heighty])
		self.window.blit(entype, [475, self.heighty])
		self.window.blit(dmgdef, [550, self.heighty])
		self.window.blit(cost, [585, self.heighty])
		self.window.blit(description, [85, self.heighty+25])
		
		if self.selected_skill.countdown > 0:
			countdown = self.game.display_text("CD {}".format(self.selected_skill.countdown),
												BLACK,
												font_size="small")
			self.window.blit(countdown, [660, self.heighty])

	def draw_warrior_info(self):
		"""
		Displays info about the selected warrior, using 'selected_warrior'
		and not chosed_warrior, since selected_warrior its only used for this job
		(holding the character for which info will)

		"""
		# Draw scroller
		self.window.blit(self.skillscroll_bg, [0, 0])


		# Get warrior info
		name = self.game.display_text(self.selected_warrior.name, BLACK, font_size="small")
		hp = self.game.display_text(
					"Health {}".format(self.selected_warrior.health), BLACK, font_size="small")
		magic = self.game.display_text(
					"Magic {}".format(self.selected_warrior.magic), BLACK, font_size="small")
		strength = self.game.display_text(
					"Strength {}".format(self.selected_warrior.strength), BLACK, font_size="small")
		spell_strength = self.game.display_text(
					"SpellStr {}".format(self.selected_warrior.spell_strength), BLACK, font_size="small")
		defense = self.game.display_text(
					"Defense {}".format(self.selected_warrior.defense), BLACK, font_size="small")
		stamina = self.game.display_text(
					"Stamina {}".format(self.selected_warrior.stamina), BLACK, font_size="small")
		if self.selected_warrior.last_defense_skill:
			defended_by = self.game.display_text(
						"Defended by {}s {}".format(self.selected_warrior.last_defense_skill.warrior.name,
													  self.selected_warrior.last_defense_skill.name)
													, BLACK, font_size="small")
		else:
			defended_by = None

		# Draw warrior info
		self.window.blit(name, [100, self.heighty])
		self.window.blit(hp, [250, self.heighty])
		self.window.blit(magic,[350, self.heighty])
		self.window.blit(stamina, [450, self.heighty])
		self.window.blit(spell_strength, [150, self.heighty + 25])
		self.window.blit(strength, [250, self.heighty + 25])
		self.window.blit(defense, [350, self.heighty + 25])
		if defended_by:
			self.window.blit(defended_by, [450, self.heighty + 25])

	def draw_correct_skill_glow(self, skill, x, y):
		"""	
		Draws the correct skill glow for the given skill.
		There are three type:
		Attack - Red,
		Defense - Blue,
		Regeneration - Green
		"""

		if skill.skilltype == "attack":
			self.window.blit(self.skill_glowing_attck, [x, y])
		elif skill.skilltype == "defense":
			self.window.blit(self.skill_glowing_def, [x, y])
		elif skill.skilltype == "regen":
			self.window.blit(self.skill_glowing_reg, [x, y])

	def draw_skill_glowing(self):
		"""
		Draws a red glow on the skills that you can choose.

		# NOW YOU CAN CHOSE ALL SKILLS, WE HAVEN'T FIXED THE SKILL
		CHOSING YET, WE'RE NOT THERE YET, WAIT FOR US THERE VERY FAST !!!
		xD
		"""

		try:
			# Draw glowing effect on all skills if not skill is chosed
			if self.current_warrior.chosed_skill is None and self.current_warrior.chosed_warrior is None:
				#### Select the skills which we can perform if we have the magic needed
				for skillname in self.current_warrior.skills:
					skill = self.current_warrior.skills[skillname]
					if skillname in self.current_warrior.allowed_skills:
						self.draw_correct_skill_glow(skill, skill.rect.x, skill.rect.y)
					else:
						self.window.blit(self.not_allowed_glowing, [skill.rect.x, skill.rect.y])
			else:
				# Draw glowing effect on clicked not allowed skill
				if self.selected_skill.name.lower() in self.current_warrior.allowed_skills:
					self.draw_correct_skill_glow(self.selected_skill,
												 self.selected_skill.rect.x,
												 self.selected_skill.rect.y)
				# # Draw glowing effect on chosed skill
				# else:
				# 	pass
				# 	# self.window.blit(self.not_allowed_glowing,
				# 	# 				[self.selected_skill.rect.x,
				# 	# 				self.selected_skill.rect.y])
		except AttributeError:
			pass

	def draw_healthbar(self):
		"""
		Draws blood an all players.
		"""

		# Draw black rects
		for warrior in self.warriors:
			pygame.draw.rect(self.window, BLACK, [self.wshift_x,
												 warrior.warrior_rect.bottom,
												 self.hpbar_width,
												 self.healthbar_shift_y])
		for ewarrior in self.enemy_warriors:
			pygame.draw.rect(self.window, BLACK, [self.ewshift_x,
												 ewarrior.warrior_rect.bottom,
												 self.hpbar_width,
												 self.healthbar_shift_y])

		# MATH STARTS HERE BITCH!
		for warrior in self.warriors + self.enemy_warriors:
			hp_percent = warrior.health * 100/warrior.start_health
			hpbar_percent = self.hpbar_width * hp_percent/self.hpbar_width
			hpbar_new_width = self.hpbar_width * hpbar_percent/100

			hp = self.game.display_text(str(warrior.health), SILVER, font_size="small")

			if warrior in self.warriors:
				pygame.draw.rect(self.window, CARMINE, [self.wshift_x,
															warrior.warrior_rect.bottom+2,
															hpbar_new_width,
															self.healthbar_shift_y-2])
				self.window.blit(hp, [self.wshift_x, warrior.warrior_rect.bottom-2])

			else:
				pygame.draw.rect(self.window, CARMINE, [self.ewshift_x,
															warrior.warrior_rect.bottom+2,
															hpbar_new_width,
															self.healthbar_shift_y-2])
				self.window.blit(hp, [self.ewshift_x, warrior.warrior_rect.bottom-2])
	def draw_warrior_glowing(self):
		"""
		Draws a red glow on the selecte warrior,
		(enemy to attack or ally to defened)
		"""

		try:
			# Draw glowing effect on all warriors if none of them
			# is yet chosed
			if self.current_warrior.chosed_warrior is None and self.current_warrior.chosed_skill:
				# If skill is 'attack' draw it only on enemies
				# otherwise if its 'defense' draw it only on allies
				if self.current_warrior.chosed_skill.skilltype == "attack":
					for enemy in self.enemy_warriors:
						self.window.blit(self.warrior_glowing,
										[enemy.warrior_rect.x,
										 enemy.warrior_rect.y])
				elif (self.current_warrior.chosed_skill.skilltype == "defense" or
					  self.current_warrior.chosed_skill.skilltype == "regen"):
					for ally in self.warriors:
						self.window.blit(self.warrior_glowing,
										[ally.warrior_rect.x,
										ally.warrior_rect.y])

			elif self.current_warrior.chosed_skill is not None and self.current_warrior.chosed_warrior is not None:
				# If current warrior chosed a skill and a warrior to attack or defend
				# draw glow on them
				self.draw_correct_skill_glow(self.current_warrior.chosed_skill,
											 self.current_warrior.chosed_skill.rect.x,
											 self.current_warrior.chosed_skill.rect.y)
				if self.current_warrior.chosed_skill.range == "single":
					self.window.blit(self.warrior_glowing,
								[self.current_warrior.chosed_warrior.warrior_rect.x,
								 self.current_warrior.chosed_warrior.warrior_rect.y])
				elif self.current_warrior.chosed_skill.range == "all":
					for warrior in self.current_warrior.chosed_warrior:
						self.window.blit(self.warrior_glowing,
										[warrior.warrior_rect.x,
										warrior.warrior_rect.y])
		except AttributeError:
			pass

	def draw_turn_info(self):
		"""
		Displays what happened last turn.
		"""
		# Centering of scroll
		scroll_center_x = self.game.center_text_x(self.turn_info_bg)

		# Shift of y
		info_shift_y = self.game.WINDOW_WIDTH/6
		info_shift_by = 25

		# Get info
		info_surfaces = []
		for info in self.turn_info:
			info_srf = self.game.display_text(info, BLACK, font_size="small")
			info_surfaces.append(info_srf)

		# Draw info
		while True:
			# Events
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					self.game.quit_game()

				if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
					return True

			# Draw scroll
			self.window.blit(self.turn_info_bg, 
							[scroll_center_x, 0])

			# Draw info
			shift = info_shift_y
			for info in info_surfaces:
				self.window.blit(info, [scroll_center_x+125, shift])
				shift += info_shift_by

			# Update
			pygame.display.update()
			self.game.clock.tick(10)

	def draw_dead_skulls(self):
		"""
		This draws a skull on the dead warriors.
		"""

		for dead_warrior in self.dead:
			self.window.blit(self.skull_img,
							[dead_warrior.warrior_rect.x,
							dead_warrior.warrior_rect.y])

	def remove_health_from_enemy(self, warrior, enemy, skill):
		"""
		Calculates the attack damage and returnes the damage done.
		"""

		# Remove health from chosed enemy
		if skill.entype == "physical":
			health_to_remove = skill.dmgdef + warrior.strength - enemy.defense
		else:
			health_to_remove = skill.dmgdef + warrior.spell_strength - enemy.defense

		if health_to_remove > 0:
			enemy.health -= health_to_remove
		else:
			health_to_remove = 0

		return health_to_remove

	def add_defense_to_ally(self, ally, skill):
		"""
		Calculates the defense needed to add to an ally and adds it.
		"""
		if ally.last_defense_skill:
			ally.defense -= ally.last_defense_skill.dmgdef
			ally.defense += skill.dmgdef
			ally.last_defense_skill = skill
			ally.being_defended = True
			ally.last_defense_turn = 3
		else:
			ally.defense += skill.dmgdef
			ally.last_defense_skill = skill
			ally.being_defended = True
			ally.last_defense_turn = 3

	def add_health_to_ally(self, ally, skill):
		"""
		Adds some health to ally/allies.
		"""

		if ally.health >= ally.max_health:
			return 0
		else:
			ally.health += skill.dmgdef
			if ally.health >= ally.max_health:
				return ally.health - ally.max_health
			else:
				return skill.dmgdef
					
	def attack_or_defend(self):
		"""
		This skill is used to 'attack' the enemies if a skill
		was put on them or 'defend' an ally or self if a defensive
		skill was chosed, basically this method removes health from
		the attacked enemy or adds defense to the ally or self
		"""

		for warrior in self.warriors:
			try:
				if warrior.chosed_skill.skilltype == "attack":
					# Attack
					# Check for skill range
					if warrior.chosed_skill.range == "single":
						# Remove health from chosed enemy
						health_to_remove = self.remove_health_from_enemy(warrior, 
																		warrior.chosed_warrior, 
																		warrior.chosed_skill)
						# Check if killed enemy
						if warrior.chosed_warrior.health <= 0:
							attack_info = "{warrior} killed {enemy} with {skill}.".format(
																					warrior=warrior.name,
																					enemy=warrior.chosed_warrior.name,
																					skill=warrior.chosed_skill.name)
						else:
							attack_info = "{warrior} attacked {enemy} with {skill} doing {damage} damage".format(
																								warrior=warrior.name,
																								enemy=warrior.chosed_warrior.name,
								   								 								skill=warrior.chosed_skill.name,
								   								 								damage=health_to_remove)
					elif warrior.chosed_skill.range == "all":
						damage_done = []
						for ewarrior in warrior.chosed_warrior:
							# Calculate damage
							health_to_remove = self.remove_health_from_enemy(warrior,
																			ewarrior,
																			warrior.chosed_skill)
							damage_done.append(health_to_remove)
						attack_info = "{warrior} attacked all enemies doing {enemies} damage.".format(
																							warrior=warrior.name,
																							enemies=damage_done)

					# Add to turn info
					self.turn_info.append(attack_info)
				elif warrior.chosed_skill.skilltype == "defense":
					# Defend

					if warrior.chosed_skill.range == "single":
						# Add defense to that player
						# If player was assigned defense earlier we remove
						# it and add the new one(THIS IS TEMPORARY(maybe))
						self.add_defense_to_ally(warrior.chosed_warrior,
												warrior.chosed_skill)

						# Add to defense info
						if warrior.chosed_warrior == warrior:
							ally_name = "himself"
						else:
							ally_name = warrior.chosed_warrior.name

						defense_info = "{warrior} defended {ally} with {skill} defending with defense {points} ".format(
																									warrior=warrior.name,
																									ally=ally_name,
																									skill=warrior.chosed_skill.name,
																									points=warrior.chosed_skill.dmgdef)
					elif warrior.chosed_skill.range == "all":
						# For all allies
						for ally in warrior.chosed_warrior:
							self.add_defense_to_ally(ally, warrior.chosed_skill)

						defense_info = "{warrior} proctected all his allies and himself with {skill}".format(
																									warrior=warrior.name,
																									skill=warrior.chosed_skill.name)
					# Add to turn info
					self.turn_info.append(defense_info)
				elif warrior.chosed_skill.skilltype == "regen":
					# Regenerate
					if warrior.chosed_skill.range == "single":
						# Add health to the warrior that chosed this skill
						self.add_health_to_ally(warrior.chosed_warrior,
												warrior.chosed_skill)

						# Add to defense info
						if warrior.chosed_warrior == warrior:
							ally_name = "himself"
						else:
							ally_name = warrior.chosed_warrior.name

						health_info = "{warrior} healed himself with {skill} by {points}".format(
																						warrior=ally_name,
																						skill=warrior.chosed_skill.name,
																						points=warrior.chosed_skill.dmgdef)
					elif warrior.chosed_skill.range == "all":
						health_to_add = []
						# Add health to all
						for ally in warrior.chosed_warrior:
							added_hp = self.add_health_to_ally(ally,
														warrior.chosed_skill)
							health_to_add.append(added_hp)

						health_info = "{warrior} healed all his allies and himself with {skill} by {points}".format(
																									warrior=warrior.name,
																									skill=warrior.chosed_skill.name,
																									points=health_to_add)
					# Add to turn info
					self.turn_info.append(health_info)

				# Remove skill cost
				energytype = warrior.chosed_skill.entype
				if energytype == "physical":
					warrior.stamina -= warrior.chosed_skill.cost
				elif energytype == "magic":
					warrior.magic -= warrior.chosed_skill.cost

				# Put skill coutdown
				warrior.chosed_skill.countdown = warrior.chosed_skill.countdown_constant

			except AttributeError as err:
				didnot_not_perform = "{warrior} decided to just stay and watch!".format(
																					warrior=warrior.name)
				self.turn_info.append(didnot_not_perform)

	def next_turn(self):
		"""
		Changes to next turn, acts the skill the user chosed,
		and then the enemy choses a skill
		"""

		# Get bast time which will be used as the time
		# to which we measure
		basetime = time.time()

		# The time that will be compared with basetime
		timenow = basetime

		# Make the attack or the defense
		self.attack_or_defend()

		# Enemies attack or defend
		for enemy in self.enemy_warriors:
			enemy_move_info = enemy.brain.make_move()
			self.turn_info.append(enemy_move_info)

		# Check for dead warriors
		self.check_for_dead()

		# Countdown defensive turns and skills
		self.defense_skills_turns_left()
		self.descrease_skills_countdown()

		# Set selectors to None
		self.current_warrior = None
		self.clicked_last = None
		self.selected_warrior = None
		self.selected_skill = None
		self.clear_warriors_selectors()

		# Regenerate allies and enemies
		self.regenerate()

		# A turn was made
		self.turn_made = True

		while timenow < basetime + self.next_turn_delay:
			# Draw
			self.window.blit(self.skillscroll_bg, [0, 0])
			self.window.blit(self.waiting_for_enemy, [100, 50])

			# Update
			pygame.display.update()
			self.game.clock.tick(15)

			# Get time
			timenow = time.time()

	def start_battle(self):
		"""
		Starts the battle.
		"""
		battle_on = True
		while battle_on:
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					self.game.quit_game()

				if event.type == pygame.KEYDOWN and event.key != pygame.K_SPACE:
					# Check if player pressed any key
					# to clear chosed skill and chosed enemy
					self.current_warrior = None
					self.clicked_last = None
					self.selected_warrior = None
					self.selected_skill = None

				elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
					# Clear placed skills
					self.clear_placed_skills()
					# Reset turn info
					self.turn_info = ["hello bitches!"]
					# Complete turn
					self.next_turn()
					self.turn += 1
					# Display turn info
					self.draw_turn_info()

				# Clear current_warriors his chosed_skill and chosed_warrior
				if event.type == pygame.MOUSEBUTTONDOWN:
					# Check if theres a current_warrior
					# and since user clicked the right mouse button
					# we clear his chosed_skill and chosed_warrior
					if event.button == 3 and self.current_warrior:
						self.current_warrior.chosed_skill = None
						self.current_warrior.chosed_warrior = None

			# Draw and update everything
			self.window.blit(Battle.background,[0,0])

			# Draw skills
			# Ma heret se skill info qe mos me pas at "flash bug"
			self.draw_skills()

			# If a warrior was clicked last we display his info
			# ElIf a skill was clicked last draw skill info
			# Else draw the player attributes
			if self.clicked_last == "warrior" and self.selected_warrior:
				self.draw_warrior_info()
			elif self.clicked_last == "skill":
				self.draw_skill_info()
			else:
				# self.draw_attributes()
				pass

			# Draw warriors
			self.draw_warriors()
			self.draw_enemy_warriors()

			# Draw skulls if any of the warriors
			# are dead
			if len(self.dead) != 0:
				self.draw_dead_skulls()

			# Draw glowing effects
			self.draw_skill_glowing()
			self.draw_warrior_glowing()

			# Draw blood
			self.draw_healthbar()

			# Check if a turn was made to display turn info
			if self.turn_made:
				# Draw display turn info scroll button
				self.window.blit(self.turn_info_btn, 
								[self.turn_info_btn_rect.x, self.turn_info_btn_rect.y])

				clicked_btn = self.game.clicked_surface_rect(self.turn_info_btn_rect)
				if clicked_btn:		
					self.draw_turn_info()

			# Check if battle is over!
			battle_over = self.check_for_winning()
			if battle_over:
				return self.won

			pygame.display.update()
			self.game.clock.tick(20)

