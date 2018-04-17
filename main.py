from base64 import b64encode, b64decode
from os import path
import json
import qrcode
import logging
import math
import numpy
import sys
import zbar
from PIL import Image

FORMATTER = logging.Formatter('%(asctime)s|%(levelname)s|%(name)s: %(message)s')
STDOUT_HANDLER = logging.StreamHandler(stream=sys.stdout)
STDOUT_HANDLER.setFormatter(FORMATTER)
FILE_HANDLER = logging.FileHandler('log.txt')
FILE_HANDLER.setFormatter(FORMATTER)

LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(STDOUT_HANDLER)
LOGGER.addHandler(FILE_HANDLER)
LOGGER.setLevel(logging.DEBUG)

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
    return res[0].data

def write_qr_code(output_file, data):
    img = qrcode.make(data)
    img.save(output_file)

def dump_file_to_qr(input_file):
    with open(input_file, 'rb') as f:
        data = f.read()
        b64_data = b64encode(data).decode('ascii')
        b64_data_len = len(b64_data)
        num_bytes = 625
        num_chunks = math.ceil(len(b64_data) / num_bytes)
        input_file_name = path.basename(input_file)

        LOGGER.debug('b64_data_len: %d', b64_data_len)
        LOGGER.debug('num_chunks: %d', num_chunks)
        LOGGER.debug('input_file_name: %s', input_file_name)

        for i in range(0, num_chunks):
            start_index = num_bytes * i
            end_index = num_bytes * (i + 1)
            output_qr_file = '{file}_q{count}.png'.format(file=input_file, count=i)

            LOGGER.debug('output_qr_file: %s', output_qr_file)
            LOGGER.debug('start_index: %d', start_index)
            LOGGER.debug('end_index: %d', end_index)

            payload = { # len = 38 w/o name and data
                'id': 0,
                'chunkNumber': i,
                'totalChunks': num_chunks - 1,
                'name': input_file_name,
                'data': b64_data[start_index:end_index] # limit is ~650. Go 625 to be safe
            }
            payload_json = json.dumps(payload, separators=(',',':'))

            LOGGER.debug('json dumps length {test}'.format(test=len(payload_json)))
            write_qr_code(output_qr_file, payload_json)

def read_file_from_qr(qr_files):
    LOGGER.debug('Parsing %d QR files', len(qr_files))
    file_data = {} # ID -> {name: fileName, data: Array of b64}
    for f in qr_files:
        qr_json = read_qr_code(f)
        qr_payload = json.loads(qr_json)

        file_id = qr_payload['id']
        chunk = qr_payload['chunkNumber']
        totalChunks = qr_payload['totalChunks']
        name = qr_payload['name']
        data = qr_payload['data']

        LOGGER.debug('qr_file: %s', f)
        LOGGER.debug('\tid: %d', file_id)
        LOGGER.debug('\tchunk: %d/%d', chunk, totalChunks)
        LOGGER.debug('\tname: %s', name)

        if not file_id in file_data:
            b64_data = [None] * (totalChunks + 1)
            file_data[file_id] = {'name': name, 'data': b64_data}
        
        file_data[file_id]['data'][chunk] = data
    for f_id, f_info in file_data.items():
        name = f_info['name']
        data = f_info['data']
        LOGGER.debug('Analyzing data for ID %d, name: %s', f_id, name)
        data_filled = all(x is not None for x in data)
        if data_filled:
            LOGGER.debug('All data present for file: %s', name)
            complete_b64 = ''.join(data)
            write_file('cloned_' + name, complete_b64)
        else:
            LOGGER.warn('Missing data for file: %s', name)

def write_file(output_file, b64_data):
    with open(output_file, 'wb') as f:
        file_data = b64decode(b64_data)
        f.write(file_data)

#dump_file_to_qr('archive.zip')
#read_file_from_qr(sys.argv[1:])