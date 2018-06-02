#!/usr/bin/env python2
import sys
import unittest
import pygame
from mock import Mock
from game import Game

pygame.init()

class GameTest(unittest.TestCase):
	def setUp(self):
		false_pygame_setmode = Mock(return_value=pygame.Surface)
		pygame.display.set_mode = false_pygame_setmode()

		window = pygame.display.set_mode((780, 640))
		self.game = Game(window)

	def tearDown(self):
		pass

	def test_helo(self):
		print "what"

if __name__ == "__main__":
	unittest.main()