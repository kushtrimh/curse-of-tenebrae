from pytmx.util_pygame import load_pygame
import pygame
from sprites import *
from worldmap import worldmap, add_kingdoms, KINGDOMS
import battle
from colors import *

class Kingdom(object):
	def __init__(self, game, window, name):
		self.game = game
		self.game.kingdom = self

		self.window = window
		self.WINDOW_WIDTH = self.window.get_width()
		self.WINDOW_HEIGHT = self.window.get_height()

		self.name = name

		self.WHITE = (255, 255, 255)

		self.lost_story = None

	def load_kingdom(self, tmx_data, background, npcs_filename):
		# Start the loading screen until needed
		# data is loaded
		with self.game.load():

			# Add to group so it can be drawn
			self.game.player_group.add(self.game.player)

			# Load map tmx_data
			self.tmx_data = load_pygame(tmx_data)

			# World // World Objects
			self.game.set_world_objects(self.tmx_data, Blocks, Buildings, Shops)
			self.game.set_world(background)
			self.game.world.name = self.name

			# Load NPCs
			self.npc_list = []
			self.moving_npc = []

			self.game.create_npcs(npcs_filename, self.npc_list, self.moving_npc)

			# Start of game
			self.direction = "down"
			self.npc_direction = "down"

			self.change_x = 0
			self.change_y = 0

			self.kingdom_on = True

			self.leave_kingdom = False
			self.kingdom_name = None

			kingdom_map_img = pygame.image.load(
									"maps/{}.png".format(self.name.lower())
									)
			self.map = pygame.transform.scale(kingdom_map_img, 
											  [self.game.WINDOW_WIDTH,
											  self.game.WINDOW_HEIGHT])

	def kingdom_life(self):		
		while self.kingdom_on:
			# Events
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					self.kingdom_on = False
					self.game.quit_game()
				if event.type == pygame.KEYDOWN:
					if event.key == pygame.K_DOWN:
						self.change_y = 5
					if event.key == pygame.K_UP:
						self.change_y = -5
					if event.key == pygame.K_RIGHT:
						self.change_x = 5
					if event.key == pygame.K_LEFT:
						self.change_x = -5
					if event.key == pygame.K_i:
						# Display profile
						self.game.show_profile()
					if event.key == pygame.K_q:
						# Display story board
						self.game.show_story_board()
					if event.key == pygame.K_l:
						# Display skills
						self.game.show_skills()
					elif event.key == pygame.K_h:
						# Display help
						self.game.show_help()
					elif event.key == pygame.K_k:
						# Display map of the current kingdom
						self.game.show_kingdom_map()
					elif event.key == pygame.K_c:
						# Display clothes and change them
						self.game.show_clothes()
						self.change_x = 0
						self.change_y = 0
					elif event.key == pygame.K_m:
						map_result = worldmap(self.game)
						self.kingdom_name = map_result[0]

						if map_result[1] == "leave":
							self.leave_kingdom = True
						elif map_result == "lost":
							# Check if lost story
							self.game.set_game()
							return True
						else:
							self.leave_kingdom = False

					elif event.key == pygame.K_SPACE and self.game.player.can_talk_to_npc != None:
						# User stops and talks with NPC
						self.game.player.talking_with_npc = True

						# Check if the npc can chat, to chat with him not only
						# run the other function, that returns shows a 'talk' of npc
						if self.game.player.can_talk_to_npc.can_chat:
							print self.game.chat_with_npc(self.game.player.can_talk_to_npc)
							self.change_x = 0
							self.change_y = 0
						else:
							if self.game.player.can_talk_to_npc:
								print self.game.player_talks_with_npc(self.game.player.can_talk_to_npc)
								self.change_x = 0
								self.change_y = 0
							
					elif event.key == pygame.K_ESCAPE:
						# Put the menu on
						# If functions returns 'mainmenu' send the game to mainmenu
						self.game.player.lead_x = 0
						self.game.player.lead_y = 0
						menuresult = self.game.menu()

				if event.type == pygame.KEYUP:
					if event.key == pygame.K_DOWN:
						self.change_y = 0
					if event.key == pygame.K_UP:
						self.change_y = 0
					if event.key == pygame.K_RIGHT:
						self.change_x = 0
					if event.key == pygame.K_LEFT:
						self.change_x = 0

			try:
				# Check if player clicked to enter to mainmenu
				if menuresult == "mainmenu":
					return True
			except UnboundLocalError:
				pass

			# Check if the user is has started the story mode
			if self.game.story is None and self.name == "Tenebrae":
				self.game.start_story_mode()
			
			# Check if user entered another kingdom through the map
			# Break the loop and run the function of the entered kingdoms
			# While ending this one
			if self.leave_kingdom:
				return self.leave_kingdom, self.kingdom_name

			# Set direction
			self.game.player.set_direction()
			for npc in self.moving_npc:
				self.npc_direction = npc.set_direction()

			# Check if it entered any building
			building = self.game.entered_building()
			if building != None:
				# Corrected position when leaving a builiding
				## First get the x and y of player before entering
				## Then when it leaves it set his position to that
				## So it's in the same position as when he entered the building
				current_x = self.game.player.rect.x
				current_y = self.game.player.rect.y
				# Enter the building
				stop_player = self.game.enter_building(building)
				# When left the building, make changes
				if stop_player:
					self.change_x = 0
					self.change_y = 0
					self.game.player.rect.x = current_x
					# Plus 15 se qe me bo pak ma larg pej dere
					self.game.player.rect.y = current_y + 15

			# Draw and update everything
			self.game.world_group.draw(self.window)
			self.game.player_group.draw(self.window)
			self.game.player.update([self.game.objects_group, 
									self.game.buildings_group , 
									self.game.npc_group])

			# Check if enetred a story
			self.game.entered_story_place("kingdom", self.game.player)

			# Update world
			self.game.world.update(self.change_x, self.change_y, self.game.npc_group)

			# Draw NPC
			self.game.npc_group.draw(self.window)
			for npc in self.moving_npc:
				npc.update_npc(self.game.objects_group, 
							   self.game.player_group, 
							   self.game.npc_group)

			# UPDATE AND CLOCK
			pygame.display.update()
			self.game.clock.tick(self.game.FPS)

	def clear(self):
		# When leaves home
		self.game.player_group.empty()
		self.game.npc_group.empty()
		self.game.objects_group.empty()
		self.game.world_group.empty()
		self.window.fill(self.WHITE)