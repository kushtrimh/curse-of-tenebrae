#!/usr/bin/env python2
import os
import StringIO
import shutil
from itertools import izip_longest
from Tkinter import *
from PIL import Image
import tkFileDialog
import tkMessageBox

class Application(object):
	def __init__(self, master):
		self.master = master
		self.master.title("CurseCreator")

		# Variables
		self.npc_file = None
		self.skill_file = None
		self.story_file = None

		self.story_enemies = []
		self.story_name = None

		# Display main munu
		self.display_main_menu()

		self.attr_list = ["health", "magic", "stamina",
					 	  "max_health", "max_magic", "max_stamina",
					 	  "spell_strength", "strength", "defense"]
		self.attributes = {}

		self.bg = "#f2f2f2"

	def get_sprites_dir(self, imagepath):
		"""
		Returns the dir of the NPC sprites if that NPC
		has a type of normal, since stoned NPCs only use
		one images.
		"""

		direction_path = os.path.dirname(imagepath)

		if "down" in direction_path or \
			"left" in direction_path or \
			"right" in direction_path or \
			"up" in direction_path:
			return os.path.dirname(direction_path)
		else:
			return imagepath


	def display_main_menu(self):
		"""
		Displays the main menu on the Tkinter Application.
		"""

		self.mainmenu = Menu(self.master)

		self.mainmenu.add_command(label="Create NPC",
								  command=self.display_npc_creator)
		self.mainmenu.add_command(label="Create Skill",
								  command=self.display_skill_creator)
		self.mainmenu.add_command(label="Create Story",
								  command=self.display_story_creator)

		self.master.config(menu=self.mainmenu)

	def ask_for_filename(self, ext=None, var=None):
		"""
		Asks for a filename and returns the absolute path
		of it.
		"""

		filename = tkFileDialog.askopenfilename(
								title="Filename",
								defaultextension=ext)
		if var:
			var.set(filename)

		if filename == "" or len(filename) == 0:
			return None
		else:
			return filename

	def clear(self, *entries):
		"""
		Deletes the text all given entries.
		"""

		for entry in entries:
			try:
				entry.delete(0, END)
			except AttributeError as err:
				tkMessageBox.showerror("AttributeError",
										str(err))

	def attribute_fixer(self, attr, value):
		if attr in self.attr_list:
			self.attributes[attr] = value
			return True
		else:
			return False

	def create_npc(self, *args, **kwargs):
		"""
		Creates a NPC line that is used in Curse of Tenebrae
		to make the NPC, this line gets written to the given
		NPC file.
		"""

		npc_line = {
			"npc_type": [0],
			"name": [1],
			"image": [2],
			"spritecount": [3],
			"x": [4],
			"y": [5],
			"communication": [6],
			"can_chat": [7],
			"skills": [8],
			"attributes": [9],
			"warrior_image": [10]
		}

		for attr, value in kwargs.iteritems():
			try:
				attr_value = value.get()
			except ValueError:
				tkMessageBox.showerror("Creation Error",
									   "Some entries accept only numbers")
				return False

			if attr_value is None:
				tkMessageBox.showerror("Creation Error",
			   						   "All attributes should be provided.")
				return False
			else:
				if self.attribute_fixer(attr, attr_value):
					pass
				elif attr == "skills":
					skills = attr_value.split(",")
					npc_line[attr].append(skills)
				else:
					npc_line[attr].append(attr_value)

		# Set image
		if npc_line["npc_type"][1] == "normal":
			sprites_dir = self.get_sprites_dir(npc_line["image"][1])
			npc_line["image"][1] = sprites_dir

		# Change image size
		warrior_img_filename = npc_line["warrior_image"][1]
		warrior_img = Image.open(warrior_img_filename)
		new_img = warrior_img.resize((130, 150), Image.ANTIALIAS)
		new_img.save(warrior_img_filename)

		# Set attributes
		npc_line["attributes"].append(self.attributes)
		npc_sorted_line = sorted(npc_line.values())
		
		final_line = ""
		for attr in npc_sorted_line:
			try:
				attr_value = attr[1]
			except IndexError:
				attr_value = []
			final_line += "{}__".format(attr_value)

		final_line = final_line[:-2] + "\n"

		if not isinstance(self.npc_file, StringIO.StringIO):
			with open(self.npc_file, "a") as fl:
				fl.write(final_line)
		else:
			self.npc_file.write(final_line)

		return True

		# Success
		tkMessageBox.showinfo("Success",
							  "NPC Line Created.")

	def display_npc_creator(self, called_by_story=False):
		"""
		Displays a new Top Level window that is used to 
		create new NPC into the given file.
		"""

		if not called_by_story:
			self.npc_file = self.ask_for_filename()
		else:
			self.npc_file = StringIO.StringIO()

		if self.npc_file == None:
			tkMessageBox.showerror("NPC File Error.",
								   "You should provide a file that"\
								   "will be used to store create NPCs.")
			return False
		else:
			# Display NPC Creator
			npc_toplevel = Toplevel()
			npc_toplevel.title("NPC Creator")

			frame = Frame(npc_toplevel)
			frame.grid(row=0, column=0)

			# Variables
			img = StringVar()
			warrior_img = StringVar()

			# Image Buttons
			open_img_btn = Button(
							frame,
							text="Open Image\n\Dir",
							command=lambda:self.ask_for_filename(var=img))
			open_warrior_img_btn = Button(
							frame,
							text="Open Warrior\nImage",
							command=lambda: self.ask_for_filename(var=warrior_img))

			open_img_btn.grid(row=0, column=0, ipadx=30)
			open_warrior_img_btn.grid(row=0, column=1, ipadx=30)

			# Type Radio Buttons
			type_label = Label(frame, text="NPC Type")
			npc_type = StringVar()

			typenormal_btn = Radiobutton(frame, text="Normal",
								   		 variable=npc_type, value="normal")
			typestoned_btn = Radiobutton(frame, text="Stoned",
										 variable=npc_type, value="stoned")

			type_label.grid(row=0, column=2)
			typenormal_btn.grid(row=1, column=2, ipadx=30, ipady=1)
			typestoned_btn.grid(row=2, column=2, ipadx=30, ipady=1)

			# Attribute Entries
			spritecount = IntVar()
			name = StringVar()
			health = IntVar()
			magic = IntVar()
			stamina = IntVar()
			max_health = IntVar()
			max_stamina = IntVar()
			max_magic = IntVar()
			strength = IntVar()
			defense = IntVar()
			spell_strength = IntVar()

			spritecount_label = Label(frame, text="Sprite Count")
			name_label = Label(frame, text="Name")
			health_label = Label(frame, text="Health")
			magic_label = Label(frame, text="Magic")
			stamina_label = Label(frame, text="Stamina")
			max_health_label = Label(frame, text="Max Health")
			max_magic_label = Label(frame, text="Max Magic")
			max_stamina_label = Label(frame, text="Max Stamina")
			strength_label = Label(frame, text="Strength")
			defense_label = Label(frame, text="Defense")
			spell_strength_label = Label(frame, text="Spell Strength")

			spritecount_entry = Entry(frame, textvariable=spritecount)
			name_entry = Entry(frame, textvariable=name)
			health_entry = Entry(frame, textvariable=health)
			magic_entry = Entry(frame, textvariable=magic)
			stamina_entry = Entry(frame, textvariable=stamina)
			max_health_entry = Entry(frame, textvariable=max_health)
			max_magic_entry = Entry(frame, textvariable=max_magic)
			max_stamina_entry = Entry(frame, textvariable=max_stamina)
			strength_entry = Entry(frame, textvariable=strength)
			defense_entry = Entry(frame, textvariable=defense)
			spell_strength_entry = Entry(frame, textvariable=spell_strength)

			# Temporary
			x_axis = IntVar()
			y_axis = IntVar()
			x_axis_label = Label(frame, text="X")
			y_axis_label = Label(frame, text="Y")
			x_axis_entry = Entry(frame, textvariable=x_axis)
			y_axis_entry = Entry(frame, textvariable=y_axis)

			x_axis_label.grid(row=9, column=0)
			x_axis_entry.grid(row=9, column=1)
			y_axis_label.grid(row=10, column=0)
			y_axis_entry.grid(row=10, column=1)


			# Display
			spritecount_label.grid(row=1, column=0)
			spritecount_entry.grid(row=1, column=1)
			name_label.grid(row=2, column=0)
			name_entry.grid(row=2, column=1)

			health_label.grid(row=3, column=0)
			health_entry.grid(row=3, column=1)
			magic_label.grid(row=4, column=0)
			magic_entry.grid(row=4, column=1)
			stamina_label.grid(row=5, column=0)
			stamina_entry.grid(row=5, column=1)

			max_health_label.grid(row=6, column=0)
			max_health_entry.grid(row=6, column=1)
			max_magic_label.grid(row=7, column=0)
			max_magic_entry.grid(row=7, column=1)
			max_stamina_label.grid(row=8, column=0)
			max_stamina_entry.grid(row=8, column=1)

			strength_label.grid(row=11, column=0)
			strength_entry.grid(row=11, column=1)
			defense_label.grid(row=12, column=0)
			defense_entry.grid(row=12, column=1)
			spell_strength_label.grid(row=13, column=0)
			spell_strength_entry.grid(row=13, column=1)

			# Communication
			communication = StringVar()
			communication_label = Label(frame,
										text="NPC Communication")

			talk_btn = Radiobutton(frame,
								   text="Talks",
								   variable=communication,
								   value="talks")
			question_btn = Radiobutton(frame,
									text="Questions",
									variable=communication,
									value="questions")

			communication_label.grid(row=14, column=0)
			talk_btn.grid(row=15, column=0)
			question_btn.grid(row=16, column=0)

			can_chat = StringVar()
			can_chat_btn = Checkbutton(frame,
									   text="Can Chat",
									   variable=can_chat,
									   onvalue="True",
									   offvalue="False")
			can_chat_btn.grid(row=17, column=1)

			# Skills
			skills = StringVar()

			skills_label = Label(frame, 
								 text="Enter skillnames seperated by ','")
			skills_entry = Entry(frame, textvariable=skills)

			skills_label.grid(row=18, column=0)
			skills_entry.grid(row=18, column=1)

			# Finish Creation
			finish_frame = Frame(npc_toplevel, borderwidth=2, relief=SUNKEN)
			finish_frame.grid(row=1, column=0)

			finish_btn = Button(finish_frame,
								text="Create,",
								command=lambda: 
										self.create_npc(
											name=name,
											health=health,
											magic=magic,
											stamina=stamina,
											max_health=max_health,
											max_magic=max_magic,
											max_stamina=max_stamina,
											npc_type=npc_type,
											image=img,
											warrior_image=warrior_img,
											x=x_axis,
											y=y_axis,
											can_chat=can_chat,
											communication=communication,
											spritecount=spritecount,
											strength=strength,
											defense=defense,
											spell_strength=spell_strength,
											skills=skills)
								)
			exit_btn = Button(finish_frame,
							  text="Exit",
							  command=npc_toplevel.destroy)
			clear_btn = Button(finish_frame,
							   text="Clear",
							   command=lambda: self.clear(
							   							name_entry,
							   							health_entry,
							   							magic_entry,
							   							stamina_entry,
							   							max_health_entry,
							   							max_magic_entry,
							   							max_stamina_entry,
							   							))

			finish_btn.grid(row=0, column=0, ipadx=50)
			clear_btn.grid(row=0, column=1, ipadx=50)
			exit_btn.grid(row=0, column=2, ipadx=50)

			if called_by_story:
				label = Label(finish_frame, text="Story Enemy Creation")
				story_btn = Button(finish_frame, text="Click to Finish",
								   command=lambda: 
								   			self._add_to_enemies(
								   					npc_toplevel)
								   )
				label.grid(row=1, column=0)
				story_btn.grid(row=1, column=1)

			localvars = locals()
			self.change_color(self.bg, localvars, False, 
							  "finish_btn", "clear_btn", "exit_btn")

	def create_skill(self, **kwargs):
		attributes = [
			(0, kwargs["name"].get()),
			(1, kwargs["image"].get()),
			(2, kwargs["skilltype"].get()),
			(3, kwargs["energytype"].get()),
			(4, kwargs["dmgdef"].get()),
			(5, kwargs["description"].get("1.0", END)),
			(6, kwargs["cost"].get()),
			(7, kwargs["countdown"].get()),
			(8, kwargs["range"].get()),
		]

		if not kwargs["image"].get().endswith(".png"):
			tkMessageBox.showerror("Only PNG images supported",
								   "Only PNG Images supported.")
			return True

		# Change image
		skill_images_path = "battle/skills"

		img = Image.open(kwargs["image"].get())
		newimg = img.resize((80, 100), Image.ANTIALIAS)

		image_path = os.path.join(skill_images_path, 
								  os.path.basename(kwargs["image"].get()))
		newimg.save(image_path)

		skilline = ""
		for index, attr in attributes:
			if index == 1:
				attr = image_path
			try:
				skilline += "{}__".format(attr.strip())
			except AttributeError:
				skilline += "{}__".format(attr)

		final_line = "{}\n".format(skilline[:-2])

		with open(self.skill_file, "a") as fl:
			fl.write(final_line)

		tkMessageBox.showinfo("Skill Created!",
							  "Skill was created successfully!")
		return True

	def change_color(self, color, localvars, reverse=False, *exclude):
		"""
		Change color of all widgets in the given function.

		*exclude is a list of parameters you don't want to change color.
		if reverse is True it changes color of all exclude elements
		"""

		for name in localvars:
			try:
				if not reverse:
					if localvars[name].__module__ == "Tkinter" and \
					name not in exclude:
						localvars[name].config(bg=color)
				else:
					if localvars[name].__module__ == "Tkinter" and \
					name in exclude:
						localvars[name].config(bg=color)
			except AttributeError:
				pass

	def display_skill_creator(self):
		"""
		Displays a top level window thats used to create
		new skills.
		"""
		
		self.skill_file = self.ask_for_filename()

		if self.skill_file is None:
			tkMessageBox.showerror("File Error",
									"A Skill file is needed"\
									" to be used for saving"\
									" new created skills.")
			return True 
		elif not self.skill_file.endswith(".txt"):
			tkMessageBox.showerror("File Error",
								   "Only '.txt' files are allowed.")
			return True
		else:
			skill_toplevel = Toplevel()

			# Frame
			frame = Frame(skill_toplevel)
			frame.grid(row=0, column=0)

			# Skill Image
			image = StringVar()
			image_btn = Button(frame,
							   text="Open Skill Image",
							   command = lambda: 
							   			self.ask_for_filename(var=image))
			image_btn.grid(row=0, column=0)

			# Name
			name = StringVar()
			name_label = Label(frame, text="Name")
			name_entry = Entry(frame, textvariable=name)

			name_label.grid(row=0, column=1)
			name_entry.grid(row=0, column=2)

			# Attributes
			# Skills type
			skilltype_label = Label(frame, text="Skill Type")

			skilltype = StringVar()

			attack_btn = Radiobutton(frame, text="Attack",
									 variable=skilltype, value="attack")
			defense_btn = Radiobutton(frame, text="Defense",
									  variable=skilltype, value="defense")
			regen_btn = Radiobutton(frame, text="Regeneration",
									  variable=skilltype, value="regen")

			skilltype_label.grid(row=1, column=0)
			attack_btn.grid(row=2, column=0)
			defense_btn.grid(row=3, column=0)
			regen_btn.grid(row=4, column=0)

			# Energy types
			energytype_label = Label(frame, text="Energy Type")

			energytype = StringVar()

			physical_btn = Radiobutton(frame, text="Physical",
										variable=energytype, value="physical")
			magic_btn = Radiobutton(frame, text="Magic",
										variable=energytype, value="magic")

			energytype_label.grid(row=1 , column=1)
			physical_btn.grid(row=2, column=1)
			magic_btn.grid(row=3, column=1)

			# Range type
			rangetype_label = Label(frame, text="Range Type")

			rangetype = StringVar()

			rall_btn = Radiobutton(frame, text="All",
								   variable=rangetype, value="all")
			rsingle_btn = Radiobutton(frame, text="Single",
									variable=rangetype, value="single")

			rangetype_label.grid(row=1, column=2)
			rall_btn.grid(row=2, column=2)
			rsingle_btn.grid(row=3, column=2)


			# Other attributes
			dmgdef = IntVar()
			dmgdef_label = Label(frame, text="Power Points(dmgdef)")
			dmgdef_entry = Entry(frame, textvariable=dmgdef)

			countdown = IntVar()
			countdown_label = Label(frame, text="Countdown")
			countdown_entry = Entry(frame, textvariable=countdown)

			cost = IntVar()
			cost_label = Label(frame, text="Cost")
			cost_entry = Entry(frame, textvariable=cost)

			dmgdef_label.grid(row=5, column=0)
			dmgdef_entry.grid(row=5, column=1)
			countdown_label.grid(row=6, column=0)
			countdown_entry.grid(row=6, column=1)
			cost_label.grid(row=7, column=0)
			cost_entry.grid(row=7, column=1)

			description_label = Label(frame, text="Description")
			description_entry = Text(frame, width=50, height=10)

			description_label.grid(row=8, column=0)
			description_entry.grid(row=9, column=0, columnspan=3)

			# Create skills
			createskill_frame = Frame(skill_toplevel)
			createskill_frame.grid(row=1, column=0)

			create_btn = Button(createskill_frame,
								text="Create",
								command=lambda: 
										self.create_skill(
											name=name,
											image=image,
											skilltype=skilltype,
											dmgdef=dmgdef,
											cost=cost,
											countdown=countdown,
											description=description_entry,
											range=rangetype,
											energytype=energytype,
										)
								)
			exit_btn = Button(createskill_frame,
							  text="Exit",
							  command=skill_toplevel.destroy)

			create_btn.grid(row=0, column=0)
			exit_btn.grid(row=0, column=1)

	# Story
	def _add_to_images(self, imgs_list):
		image = self.ask_for_filename()
		
		filename, ext = os.path.splitext(image)

		if ext.lower() in [".png", ".jpg", ".jpeg", ".gif"]:
			imgs_list.append(image)
			print imgs_list
		else:
			tkMessageBox.showerror("Error",
								   "Only 'png, jpg and gif' are supported.")
	def _create_enemies(self, enemy_list):
		self.display_npc_creator(True)

	def _add_to_enemies(self, npc_toplevel):
		rawenemy = self.npc_file.getvalue()
		
		enemy_splitted = rawenemy.strip().split("__")
		enemy = "=".join(enemy_splitted).replace("==", "=")
		self.story_enemies.append(enemy)

		npc_toplevel.destroy()

	def display_story_creator(self):
		# Get story name
		story_toplevel = Toplevel()

		frame = Frame(story_toplevel)
		frame.grid(row=0, column=0)

		# Attributes
		terrain_lbl = Label(frame, text="Terrain")

		terrain = StringVar()
		map_terrain = Radiobutton(frame,
								  variable=terrain,
								  value="map",
								  text="Map")
		kingdom_terrain = Radiobutton(frame,
									variable=terrain,
									value="kingdom",
									text="Kingdom")

		# Place
		xplace = IntVar()
		yplace = IntVar()
		widthplace = IntVar()
		heightplace = IntVar()

		place_lbl = Label(frame, text="Place")
		xplace_lbl = Label(frame, text="X")
		yplace_lbl = Label(frame, text="Y")
		widthplace_lbl = Label(frame, text="Width")
		heightplace_lbl = Label(frame, text="Height")

		xplace_entry = Entry(frame, textvariable=xplace)
		yplace_entry = Entry(frame, textvariable=yplace)
		widthplace_entry = Entry(frame, textvariable=widthplace)
		heightplace_entry = Entry(frame, textvariable=heightplace)

		# Images
		images_lbl = Label(frame, text="Story Images")

		beggining_images = []
		middle_images = []
		ending_images = []

		beggining_button =  Button(frame, 
								   text="Add img to beggining images",
								   command=lambda: self._add_to_images(
								   						beggining_images)
								   )
		middle_button = Button(frame, 
			 				   text="Add img to middle part images",
							   command=lambda: self._add_to_images(
														middle_images)
							   )
		ending_button = Button(frame, 
							   text="Add to img to story ending",
							   command=lambda: self._add_to_images(
														ending_images)
							   )

		# Enemies
		enemies_lbl = Label(frame, text="Enemies")

		enemies = []
		enemies_btn = Button(frame, 
							 text="Add enemies",
							 command=lambda: self._create_enemies(enemies))

		reward = IntVar()
		rewards_lbl = Label(frame, text="Money Reward")
		rewards_entry = Entry(frame, textvariable=reward)

		skill_rewards = StringVar()
		skill_rewards_lbl = Label(frame, text="Skill Rewards")
		skill_rewards_entry = Entry(frame, textvariable=skill_rewards)

		# Display on toplevel
		terrain_lbl.grid(row=0, column=0)
		map_terrain.grid(row=1, column=0)
		kingdom_terrain.grid(row=2, column=0)

		place_lbl.grid(row=0, column=1)
		xplace_lbl.grid(row=1, column=1)
		xplace_entry.grid(row=1, column=2)
		yplace_lbl.grid(row=2, column=1)
		yplace_entry.grid(row=2, column=2)
		widthplace_lbl.grid(row=3, column=1)
		widthplace_entry.grid(row=3, column=2)
		heightplace_lbl.grid(row=4, column=1)
		heightplace_entry.grid(row=4, column=2)

		images_lbl.grid(row=5, column=0)
		beggining_button.grid(row=6, column=0)
		middle_button.grid(row=7, column=0)
		ending_button.grid(row=8, column=0)

		enemies_lbl.grid(row=9, column=0)
		enemies_btn.grid(row=10, column=0)

		rewards_lbl.grid(row=11, column=0)
		rewards_entry.grid(row=12, column=0)

		skill_rewards_lbl.grid(row=13, column=0)
		skill_rewards_entry.grid(row=14, column=0)

		# Finish frame
		finish_frame = Frame(story_toplevel, 
							 relief=SUNKEN, bd=1,
							 padx=100)
		finish_frame.grid(row=1, column=0)

		storyname = StringVar()
		storyname_lbl = Label(finish_frame, text="Story Name")
		storyname_entry = Entry(finish_frame, textvariable=storyname)

		finish_btn = Button(finish_frame,
							text="Create Story",
							command=
								lambda:
									self.create_story(
										terrain=terrain.get(),
										x=xplace.get(),
										y=yplace.get(),
										width=widthplace.get(),
										height=heightplace.get(),
										beggining_images=beggining_images,
										middle_images=middle_images,
										ending_images=ending_images,
										enemies=self.story_enemies,
										reward=reward.get(),
										skills=skill_rewards.get(),
										name=storyname.get()
													)
							)
		storyname_lbl.grid(row=0, column=0)
		storyname_entry.grid(row=0, column=1)
		finish_btn.grid(row=1, column=0)

	def create_story(self, **kwargs):
		"""
		'beg' for beggining xD.
		"""
		if kwargs["name"] == "" or kwargs["name"].isspace():
			tkMessageBox.showerror("StoryError", 
									"A Story must have a name!")
			return False

		# Create story folder
		story_name = "_".join(kwargs["name"].split(" ")).lower()
		try:
			os.mkdir("story/{}".format(story_name))
		except OSError:
			pass

		index = 1

		story_attrs = [
			(0, ("terrain", kwargs["terrain"])),
			(index, ("place", (kwargs["x"], kwargs["y"], 
					  			kwargs["width"], kwargs["height"]))),
		]


		# Add images
		for counter, (beg, mid, end) in enumerate(izip_longest(
												   kwargs["beggining_images"],
										  		   kwargs["middle_images"],
												   kwargs["ending_images"])
												):
			try:
				if beg:
					index += 1
					story_attrs.append((index, ("bimg{}".format(counter), os.path.basename(beg))))
					shutil.copy(beg, os.path.join("story", story_name, os.path.basename(beg)))
				if mid:
					index += 1
					story_attrs.append((index, ("mimg{}".format(counter),  os.path.basename(mid))))
					shutil.copy(beg, os.path.join("story", story_name, os.path.basename(mid)))
				if end:
					index += 1
					story_attrs.append((index, ("eimg{}".format(counter), os.path.basename(end))))
					shutil.copy(beg, os.path.join("story", story_name, os.path.basename(end)))
			except TypeError:
				pass

		# Add enemies
		for c, enemy in enumerate(kwargs["enemies"]):
			index += 1
			story_attrs.append((index, ("enemy{}".format(c), enemy)))

		# Add reward
		reward = [("self.game.player.items['Money']", kwargs["reward"])]
		index += 1
		story_attrs.append((index, ("reward", reward)))

		# Add skills
		skillnames = kwargs["skills"].split(",")
		skills = []

		for skill in skillnames:
			skills.append("self.game.player.set_skills(['{}'])".format(skill))

		index += 1
		story_attrs.append((index, ("skills", skills)))

		with open(os.path.join("story", story_name, "storydata.txt"), "w") as f:
			for index, (name, value) in story_attrs:
				f.write("{}__{}\n".format(name, value))

		# Add to wholestory
		with open("story/wholestory.txt", "a") as fl:
			fl.write("{}\n".format(story_name))

		tkMessageBox.showinfo("Created", "Story Created!")
		return True

if __name__ == "__main__":
	root = Tk()
	app = Application(root)
	root.mainloop()