import pygame
import os

def get_images_with_directions(path, 
							   largest_image_num,
							   format="png", 
							   image_name=None):
	"""
	Sets all images to according directions,
	a dictionary gets returned containing 'directions' 
	as keys and lists of images as values

	path -- Inside the path should be 4 folders, named 
	        'left, right, down, up'
	largest_image_num -- images start from 0, largest_image_num
	                     should be the largest number
						 that the images have on the name
	format -- format of images, default is png
	image_name -- if images have any name with their numbers, 
				  it should be put here
	"""

	folder_names = ["down", "up", "left", "right"]

	images_with_directions = {}

	# Go into each folder
	for direction_folder in folder_names:
		# Group path with folder
		image_path =  "{}/{}".format(path, direction_folder)

		single_direction_images = []
		# Go for each image
		for num in range(largest_image_num+1):
			if image_name == None:
				image_full_path = "{}/{}.{}".format(image_path, 
													num, 
													format)
				# Load image in pygame
				try:
					image = pygame.image.load(image_full_path)
					single_direction_images.append(image)
				except pygame.error as err:
					raise Exception(str(err))

			else:
				image_full_path = "{}/{}{}.{}".format(image_path, 
													  image_name, 
													  num, 
													  format)
				try:
					image = pygame.image.load(image_full_path)
					single_direction_images.append(image)
				except pygame.error as err:
					raise Exception(str(err))

		# Add direction with loaded images to dictionary
		images_with_directions[direction_folder] = single_direction_images
	
	return images_with_directions

def get_objects_from_tmx(tmx_data, sprite, world_rect=None):
	"""
	tmx_data -- The data returned from loaded the tmx file
	sprite -- The sprite with which the objects will be created
	"""

	if world_rect != None:
		world_x, world_y = world_rect
	else:
		world_x = world_y = 0

	blocks_group = pygame.sprite.Group()
	for obj in tmx_data.objects:
		if obj.name == None:
			rect = (obj.x + world_x, obj.y + world_y, obj.width, obj.height)
			block = sprite(rect, obj.name)
			blocks_group.add(block)

	return blocks_group

def get_objects_with_name_from_tmx(tmx_data, sprite, world_rect=None, shop_sprite=None, dictionary=None):
	"""
	tmx_data -- The data returned from loaded the tmx file
	sprite -- The sprite with which the objects will be created
	dictionary -- The dictionary in which names with sprites are saved
	"""
	### All shops are named have the 'shop' suffix

	if world_rect != None:
		world_x, world_y = world_rect
	else:
		world_x = world_y = 0

	buildings_group = pygame.sprite.Group()
	shop = False

	for obj in tmx_data.objects:
		if obj.name != None:
			rect = (obj.x + world_x, obj.y + world_y, obj.width, obj.height)
			building = sprite(rect, obj.name)

			# Check if building it's a shop
			# If it is then make a Shop instance for it
			if "shop" in obj.name:
				shop = shop_sprite(building)
				building.set_shop(shop)
			else:
				shop = None

			if "cloth" in obj.name:
				building.cloth_shop = True

			buildings_group.add(building)
			if dictionary != None:
				dictionary[obj.name] = building
	return buildings_group

def get_clothe_images(path):
	"""
	Gets the images of clothes and returns a dictionary containing
	their direction and image for that direction
	"""

	# Dictionary
	images = {}

	directions = ["down", "up", "left", "right"]

	# Get images
	for direction in directions:
		direction_path = os.path.join(path, direction)
		image_path = "{}.png".format(direction_path)
		images[direction] = pygame.image.load(image_path).convert_alpha()

	return images

if __name__ == "__main__":
	# v = set_images_with_directions("ct", 8)
	# for img_list in v:
	# 	for img in v[img_list]:
	# 		print img
	v = get_clothe_images("clothes/goldragon")
	print v