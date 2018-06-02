from random import choice


class NPCBrain(object):
	"""
	This class is used to set a 'brain' to the Enemies that is used
	in the battle system
	"""

	def __init__(self, battle, npc, allies, enemies):
		"""
		!!! IMPORTANT
		!!! READ

		Since this is used only on 'enemies' in this class when we
		refer to enemies we're refering to our players. Allies are the 
		allies of this enemy, and npc is the enemy itself
		"""

		# Set all
		self.battle = battle
		self.npc = npc

		# NPC Skills
		self.skills = npc.skills

		# Health standard
		self.health_standard = self.npc.health/5


	def gather_information(self):
		"""
		Gathers information about the game, that'll be used
		for attacking or defending.
		"""

		self.enemies = self.battle.warriors

		# We don't add this NPC to his allies group because hes
		# a part of his allies since we an instance of him
		# as 'self.npc'
		self.allies = []
		for ally in self.battle.enemy_warriors:
			if ally is not self.npc:
				self.allies.append(ally)

		# Self Attributes
		# Those attributes are set likes this
		# Just for easier use
		# So we don't get to write self.npc.heath
		# BUT if you want to add or sub from NPC attributes
		# you have to use 'self.npc.attributename' not ;self.attributename'
		self.health = self.npc.health
		self.magic = self.npc.magic
		self.strength = self.npc.strength
		self.defezse = self.npc.defense
		self.spell_strength = self.npc.spell_strength
		self.being_defended = self.npc.being_defended
		self.last_defense_skill = self.npc.last_defense_skill

		# Enemy information
		self.enemies_info = {}
		for enemy in self.enemies:
			enemy_attrs = {
				"name": enemy.name,
				"health": enemy.health,
				"magic": enemy.magic,
				"strength": enemy.strength,
				"defense": enemy.defense,
				"placed_skills": enemy.placed_skills,
				"being_defened": enemy.being_defended
			}
			self.enemies_info[enemy.name] = enemy_attrs

		# Allies information
		self.allies_info = {}
		for ally in self.allies:
			ally_attrs = {
				"name": ally.name,
				"health": ally.health,
				"magic": ally.magic,
				"strength": ally.strength,
				"defense": ally.defense,
				"placed_skills": ally.placed_skills,
				"being_defened": ally.being_defended
			}
			self.allies_info[ally.name] = ally_attrs

	def move_info(self, skill, ally_or_enemy):
		"""
		This returns the info that will be display on 'turn info'.
		The info tells who player attacked or defended.
		"""

		skilltype = skill.skilltype

		if skilltype == "attack":
			text = "{self} attacked {enemy} with {skillname} causing {points} damage".format(
																						self=self.npc.name,
																						enemy=ally_or_enemy.name,
																						skillname=skill.name,
																						points=skill.dmgdef)
			return text
		elif skilltype == "defense":
			text = "{self} defened {ally} with {skillname} increasing defense by {points}".format(
																						self=self.npc.name,
																						ally=ally_or_enemy.name,
																						skillname=skill.name,
																						points=skill.dmgdef)
			return text


	def decide_move(self):
		"""
		Looks at all the possibilities and decides what to do.
		"""

		# Just attack an enemy TEST
		# Get a skill
		skill = choice(self.npc.skills.values())

		# Get an enemy
		enemy = choice(self.enemies)

		return self.move_info(skill, enemy)

	def attack_or_defend(self, skill=None, warrior=None, skilltype=None):
		"""
		Performs the move the player chosed and returns the info
		of that move.
		"""

		move_info = None


		try:
			# Calculate cost
			if skill.entype == "physical":
				self.npc.stamina -= skill.cost
			elif skill.entype == "magic":
				self.npc.magic -= skill.cost
		except AttributeError:
			pass

		# Put skill coutdown
		skill.countdown = skill.countdown_constant

		if skilltype == "attack":
			if skill.range == "single":
				# Remove health from chosed warrior
				removed_health = self.battle.remove_health_from_enemy(self,
																	 warrior,
																	 skill)

				# Check if killed enemy
				if warrior.health <= 0:
					move_info = "{self} killed {enemy} with {skillname}.".format(
																			self=self.npc.name,
																			enemy=warrior.name,
																			skillname=skill.name)
				else:
					move_info = "{self} attacked {enemy} with {skillname} causing {points} damage".format(
																								self=self.npc.name,
																								enemy=warrior.name,
																								skillname=skill.name,
																								points=removed_health)
			elif skill.range == "all":
				# Remove health from all enenmies
				removed_health_lst = []
				for enemy in self.enemies:
					removed_health = self.battle.remove_health_from_enemy(self,
																		 enemy,
																		 skill)
					removed_health_lst.append(removed_health)
				move_info = "{self} attack all enemies with {skillname} causing {dmg} damage.".format(
																								self=self.npc.name,
																								skillname=skill.name,
																								dmg=removed_health_lst
																								)
			return move_info

		elif skilltype == "defense":
			if skill.range == "single":
				# Add defense
				self.battle.add_defense_to_ally(warrior, skill)

				if warrior == self.npc:
					move_info = "{self} defened himself with {skillname} increasing defense by {points}".format(
																								self=self.npc.name,
																								skillname=skill.name,
																								points=skill.dmgdef)
				else:
					move_info = "{self} defened {ally} with {skillname} increasing defense by {points}".format(
																								self=self.npc.name,
																								ally=warrior.name,
																								skillname=skill.name,
																								points=skill.dmgdef)
				return move_info
			elif skill.range == "all":
				# Add defense to all allies
				for ally in self.allies:
					self.battle.add_defense_to_ally(ally, skill)

				move_info = "{self} defended all his allies with {skillname}.".format(
																				self=self.npc.name,
																				skillname=skill.name)

			return move_info

		elif skilltype == "regen":
			if skll.range == "single":
				# Add health to one
				self.battle.add_health_to_ally(warrior, skill)

				if self.npc == warrior:
					allyname = "himself"
				else:
					allyname = warrior.name

				move_info = "{self} healed {allyname} with {skillname}".format(
																			self=self.npc.name,
																			allyname=allyname,
																			skillname=skill.name)
				return move_info

			elif skill.range == "all":
				# Add health
				allies_health_added = []
				for ally in self.allies:
					hp_added = self.battle.add_health_to_ally(ally, skill)
					allies_health_added.append(hp_added)

				move_info = "{self} healed all his allies with {skillname} by {points}!".format(
																				self=self.npc.name,
																				skillname=skill.name,
																				points=allies_health_added)
			return move_info
		else:
			# THIS IS WHERE OUR EXCEPTION GOES xD
			return "shit!"

	def make_move(self):
		"""
		This NPC looks at all the possibilities and decides what to do.
		Whenever to attack or defend.

		THIS MAKES THE NPC'S THINK BABY!
		"""
		# Set skills we can perform
		self.npc.set_allowed_skills()

		# Gather information
		self.gather_information()

		# Check for dead warriors
		self.battle.check_for_dead()

		# MOVE 1
		# Check if theres an enemy which HP is lower than any of the skills
		# we can perform, and if theres one, ATTACK HIM!
		enemy_with_lowest_hp = None
		skill_to_perform = None
		for enemy in self.enemies:
			for skill in self.npc.allowed_skills.itervalues():
				if (skill.dmgdef > enemy.health + enemy.defense and
				 skill.skilltype == "attack"):
					# Set enemy and skill
					enemy_with_lowest_hp = enemy
					skill_to_perform = skill

				# Check if this enemy health is lower than the last enemy health
				# and if so change them
				try:
					if enemy.health < enemy_with_lowest_hp.health:
						enemy_with_lowest_hp = enemy
				except AttributeError:
					pass

				# Check if there is anyother skill whith lower cost
				# which will work to kill that enemy
				try:
					if (skill.cost < skill_to_perform.cost and 
						skill.dmgdef > enemy_with_lowest_hp.health + enemy_with_lowest_hp.defense and 
						skill.skilltype == "attack"):
						# Change skill
						skill_to_perform = skill
				except AttributeError:
					pass

		if enemy_with_lowest_hp and skill_to_perform:
			# Add skill to enemy placed skills
			enemy_with_lowest_hp.placed_skills.append(skill_to_perform)
			# print "MOVE 1 WORKS!"
			return self.attack_or_defend(warrior=enemy_with_lowest_hp,
										skill=skill_to_perform,
										skilltype="attack")

		# MOVE 2
		# Check if health is below standard so we help ourself
		skill_to_perform = None
		if self.health < self.health_standard:
			for skill in self.npc.allowed_skills.itervalues():
				# Chose the skill with the most defense which we can
				# perform

				if skill.skilltype == "defense":
					skill_to_perform = skill

				# Check if this skill adds more defense than
				# the last one
				try:
					if skill.dmgdef > skill_to_perform.dmgdef:
						skill_to_perform = skill
				except AttributeError:
					pass

				# Check if it's being defended
				# And if any of the skills has higher defense points
				# Than the defense he already
				try:
					if self.being_defended:
						if self.last_defense_skill.dmgdef >= skill_to_perform.dmgdef:
							skill_to_perform = None
				except AttributeError:
					pass


		if skill_to_perform:
			# print "MOVE 2 WORKS!"
			return self.attack_or_defend(warrior=self.npc,
										skill=skill_to_perform,
										skilltype="defense")


		# MOVE 3
		# Check if theres an ally which health is below 
		# the standard of helping him
		skill_to_perform = None
		ally_to_help = None
		for ally in self.allies:
			if ally.health < ally.brain.health_standard:
				for skill in self.npc.allowed_skills.itervalues():
					if skill.skilltype == "defense":
						# Set ally to help and skill
						skill_to_perform = skill
						ally_to_help = ally

					# Check if theres an ally whos health is lower
					try:
						if ally.health + ally.defense < ally_to_help.health + ally_to_help.defense:
							ally_to_help = ally
					except AttributeError:
						pass

					# Check if theres any other skill whith higher defense points
					# that we can use to help the ally
					try:
						if skill.skilltype == "defense" and skill.dmgdef > skill_to_perform.dmgdef:
							skill_to_perform = skill
					except AttributeError:
						pass

					# Check if ally is being defended
					# And if any of the skills has higher defense
					# Than the defense he already has
					try:
						if ally.being_defended:
							if ally.last_defense_skill.dmgdef >= skill_to_perform.dmgdef:
								skill_to_perform = None
					except AttributeError:
						pass

		if skill_to_perform and ally_to_help:
			# print "MOVE 3 WORKS!"
			return self.attack_or_defend(warrior=ally_to_help,
										skill=skill_to_perform,
										skilltype="defense")

		# MOVE 4
		# Check if we AI can heal himself
		skill_to_perform = None
		if self.health < self.npc.max_health/4:
			for skill in self.npc.allowed_skills.itervalues():
				if skill.skilltype == "regen":
					# Set skill
					skill_to_perform = skill

				try:
					if skill.dmgdef > skill_to_perform.dmgdef:
						skill_to_perform = skill
				except AttributeError:
					pass

		if skill_to_perform:
			return self.attack_or_defend(warrior=self.npc,
										skill=skill_to_perform,
										skilltype="regen")


		# MOVE 5
		# Check if there are allies to heal
		skill_to_perform = None
		ally_to_heal = None
		for ally in self.allies:
			if ally.health < ally.max_health/4:
				ally_to_heal = ally
				for skill in self.npc.allowed_skills:
					if skill.skilltype == "regen":
						skill_to_perform = skill

					try:
						if skill.dmgdef > skill_to_perform.dmgdef:
							skill_to_perform = skill
					except AttributeError:
						pass

				try:
					if ally_to_heal.health > ally.health:
						ally_to_heal = ally
				except AttributeError:
					pass

		if skill_to_perform and ally_to_heal:
			return self.attack_or_defend(warrior=ally_to_help,
										 skill=skill_to_perform,
										 skilltype="regen")


		# MOVE 6
		# Check for enemies with placed_skills on them
		skill_to_perform = None
		enemy_to_attack = None
		for enemy in self.enemies:
			if len(enemy.placed_skills) > 0:
				for skill in self.npc.allowed_skills.itervalues():
					if skill.skilltype == "attack":
						# Set skill and enemy
						skill_to_perform = skill
						enemy_to_attack = enemy

					# Check if there an enemy with higher placed skills
					# or lower hp
					try:
						if (len(enemy.placed_skills) > len(enemy_to_attack.placed_skills) or
							len(enemy.placed_skills) == len(enemy_to_attack.placed_skills) and 
							enemy.health + enemy.defense < enemy_to_attack.health + enemy_to_attack.defense):
							# Set new enemy to attack
							enemy_to_attack = enemy
					except AttributeError:
						pass

					# Check if theres a skill that does more damage
					try:
						if skill.dmgdef >= skill_to_perform.dmgdef:
							skill_to_perform = skill
					except AttributeError:
						pass

		if skill_to_perform and enemy_to_attack:
			# Add skill to placed skills
			enemy_to_attack.placed_skills.append(skill_to_perform)
			# print "MOVE 4 WORKS!"
			return self.attack_or_defend(warrior=enemy_to_attack,
										skill=skill_to_perform,
										skilltype="attack")


		# MOVE 7
		# Get and attack the enemy which health is lowest
		enemy_to_attack = None
		skill_to_perform = None
		for enemy in self.enemies:
			for skill in self.npc.allowed_skills.itervalues():
				if skill.skilltype == "attack":
					enemy_to_attack = enemy
					skill_to_perform = skill

				# Check if theres a skill that does more damage
				try:
					if skill.dmgdef > skill_to_perform.dmgdef:
						skill_to_perform = skill
				except AttributeError:
					pass

				# Check if theres an enemy with lower health
				try:
					if (enemy.health + enemy.defense < \
						enemy_to_attack.health + enemy_to_attack.defense):
						# Set enemy with lower health
						enemy_to_attack = enemy
				except AttributeError:
					pass

		if enemy_to_attack and skill_to_perform:
			# Add skill to enemy placed skills
			enemy_to_attack.placed_skills.append(skill_to_perform)
			# print "MOVE 5 WORKS!"
			return self.attack_or_defend(warrior=enemy_to_attack,
										skill=skill_to_perform,
										skilltype="attack")



