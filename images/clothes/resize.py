import Image
import os

x, y = 146, 260

lst = os.listdir(os.getcwd())
print lst
lst.remove("resize.py")

for img in lst:
	outfile = os.path.splitext(img)[0] + ".thumbnail"
	im = Image.open(img)
	im = im.resize((x, y), Image.ANTIALIAS)
	im.save(img, "PNG")