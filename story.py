"""
This module contains all the story logic.
"""

import os
import pygame
import main
import battle

WHOLESTORY_FILENAME = "story/wholestory.txt"
STORY_PATH = "story"

class Story(object):
	def __init__(self, game, name, seen_beggining=False):

		self.game = game

		self._name = name
		self.name = " ".join(name.split("_"))
		self.path = os.path.join(STORY_PATH, name)
		
		# Load all story data
		self.load_story_data()
		
		# Display Story beggining
		self.seen_beggining = seen_beggining
		if not self.seen_beggining:
			self.display_story_images("beggining")

		# Story hint
		# The red-alpha circle displayed as a hint
		hint_image = pygame.image.load("images/hint.png").convert_alpha()
		self.hint = pygame.transform.scale(hint_image, (self.place.width, self.place.height))

	def load_story_data(self):
		""""""
		with open(os.path.join(self.path, "storydata.txt")) as fl:
			storydata = fl.readlines()

		self.data = {}
		# Set story data
		for data in storydata:
			key, value = data.split("__")
			self.data[key] = value

		# Set images and enemies
		self.beggining_images = []
		self.middle_images = []
		self.ending_images = []

		self.enemies = []

		for key, value in self.data.iteritems():
			if value.endswith("\n"):
				value = value[:-1]

			if key.startswith("b") and "img" in key:
				self.beggining_images.append(
						pygame.image.load(os.path.join(self.path, value)).convert_alpha()
						)
			elif key.startswith("m") and "img" in key:
				self.middle_images.append(
						pygame.image.load(os.path.join(self.path, value)).convert_alpha()
						)
			elif key.startswith("e") and "img" in key:
				self.ending_images.append(
						pygame.image.load(os.path.join(self.path, value)).convert_alpha()
						)
			elif "enemy" in key:
				npc = self.game.make_npc(value, delimiter="=")
				self.enemies.append(npc)

			try:
				self.data[key] = value.strip()
			except AttributeError:
				pass
		
		# Set data
		self.terrain = self.data["terrain"]
		self.place = pygame.Rect(eval(self.data["place"]))
		self.description = self.data["description"]
		self.reward = self.data["reward"]
		self.skills_reward = self.data["skills"]

	def story_event_handler(self, index):
		"""
		Handles events about displaying the next image.
		"""

		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				self.game.quit_game()
			if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
				return index+1

		return index

	def display_story_images(self, part):
		""""
		Display images when this Story instance is created.
		"""

		if part == "beggining" and not self.seen_beggining:
			beggining_images_count = len(self.beggining_images)
			current_part = self.beggining_images
			image_count = beggining_images_count
		elif part == "middle":
			middle_images_count = len(self.middle_images)
			current_part = self.middle_images
			image_count = middle_images_count
		elif part == "ending":
			ending_images_count = len(self.ending_images)
			current_part = self.ending_images
			image_count = ending_images_count

		index = 0

		while index < image_count:
			# Display image
			self.game.window.blit(current_part[index], [0, 0])
			# Get new index
			index = self.story_event_handler(index)
			# Update
			pygame.display.update()
			self.game.clock.tick(15)

	def give_reward(self):
		"""
		Give reward to player.
		"""

		reward_tuple = eval(self.reward)
		for reward in reward_tuple:
			try:
				attr, attr_reward = reward
				eval_attr = "{} += {}".format(attr, attr_reward)
				exec(eval_attr)
			except ValueError:
				exec(reward)

		skills_reward = eval(self.skills_reward)
		for skill in skills_reward:
			print skill
			try:
				eval(skill)
			except ValueError as err:
				print str(err) 

	def start_story_battle(self):
		"""
		Starts a battle with the story enemies and allies.
		"""
		story_battle = battle.Battle(self.game, [self.game.player], self.enemies)
		battle_result = story_battle.start_battle()
		if battle_result:
			return True
		else:
			return False

	def begin_story(self):
		"""
		This is the function that runs the main part
		of the story, this is where the action of the story goes.
		The fighting.
		"""

		# Show middle images
		self.display_story_images("middle")

		# Start battle, test
		story_result = self.start_story_battle()

		if story_result:
			self.display_story_images("ending")
			self.give_reward()
			self.game.set_next_story()
			return story_result
		
		return story_result


