"""
This module holds the exceptions used by Curse of Tenebrae
"""

class GameError(Exception):
	"""Base Class for all Curse of Tenebrae exceptions"""
	pass

class SkillError(GameError):
	"""Exception raised for errors in skill creation"""
	pass

class NPCError(GameError):
	"""Exception raised for errors in NPC loading and creation"""
	pass
