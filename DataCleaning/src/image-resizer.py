# Importing Image class from PIL module
from PIL import Image

IMAGE_DIRECTORY = '/train/Fight/'

# Opens a image in RGB mode
sample_file = IMAGE_DIRECTORY + "Fight_2.jpg"
im = Image.open(sample_file)

# Size of the image in pixels (size of original image)
# (This is not mandatory)
width, height = im.size
print("Current image is ", im.size)
# Setting the points for cropped image
# left = 4
# top = height / 5
# right = 154
# bottom = 3 * height / 5

# Cropped image of above dimension
# (It will not change original image)
# im1 = im.crop((left, top, right, bottom))
#newsize = (512, 512)
#im1 = im.resize(newsize)

# slice the sides off to make it square
new_width = 1536
new_height = 1536
left = (width - new_width)/2
top = (height - new_height)/2
right = (width + new_width)/2
bottom = (height + new_height)/2

# Crop the center of the image
im1 = im.crop((left, top, right, bottom))

# Cropped image of above dimension
# (It will not change original image)
# im1 = im.crop((left, top, right, bottom))
newsize = (512, 512)
im2 = im1.resize(newsize)

# Shows the image in image viewer
im2.show()
