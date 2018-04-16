import qrcode
import numpy
import zbar
from PIL import Image

scanner = zbar.Scanner()

def read_qr_code(image_file):
    # Load image.
    image = Image.open(image_file)

    # We must convert the image to greyscale. However, any parts of the
    # image that contain an alpha channel are converted to black. Thus,
    # we replace the transparency with white before converting to
    # greyscale.
    if image.mode is 'RGBA':
        white_bg = Image.new('RGBA', image.size, (255, 255, 255))
        image = Image.alpha_composite(white_bg, image)
    image = image.convert('L') # L = greyscale

    # 2D numpy array of uint8
    pix = numpy.array(image)

    # parse
    res = scanner.scan(pix)
    for symbol in res:
        print('decoded {type} symbol {data}'.format(type=symbol.type, data=symbol.data))

def write_qr_code(output_file, data):
    img = qrcode.make(data)
    img.save(output_file)

write_qr_code('output.png', 'this is a test')
read_qr_code('output.png')
