from PIL import Image

im = Image.open('images/rgb.jpg')
print(im.format, im.size, im.mode)
