''' Contains utilities to convert QR codes back to files.
'''
import json
import logging
import os
import sys
from base64 import b64decode

import numpy
import zbar
from PIL import Image

from .utils import confirm_dir

LOGGER = logging.getLogger(__name__)

# The QR code scanner.
SCANNER = zbar.Scanner()

def read_qr_code(image_file):
    ''' Reads QR codes from the indicated image file and returns a list of data.

    Parameters:
      image_file <string> The image file to read.

    Returns:
      List<string> The string contained in each detected QR code.
    '''
    # Load image.
    try:
        image = Image.open(image_file)
    except OSError:
        print('File "{f}" doesn\'t appear to be an image... skipping.'.format(f=image_file))
        return []

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

    # Parse QR codes in the image
    res = SCANNER.scan(pix)

    # Extract data
    return [r.data for r in res]

def reconstruct_files_from_qr(qr_files, output_directory=''):
    ''' Reconstructs files from a list of QR codes.

    QR codes containing multiple files may be passed into this function, and
    each file will be written as expected.

    A file is only constructed if all of its QR codes are present.

    Parameters:
      qr_files List<string> A list of QR file paths.
      output_directory <string> [Optional] The directory to save the reconstructed files.
        This directory is created if it doesn't exist.
    '''
    # Try to create the output directory if it doesn't exist.
    if not confirm_dir(output_directory):
        LOGGER.warn('Failed to create output directory: %s', output_directory)
        return

    LOGGER.debug('Parsing %d QR files', len(qr_files))
    file_data = {} # FileName -> {name: fileName, data: Array of b64}
    for f in qr_files:
        # Read image and detect QR codes contained within
        qr_json_list = read_qr_code(f)
        LOGGER.debug('Found %d QR codes in file %s', len(qr_json_list), f)

        # For each QR found in the image
        for qr_json in qr_json_list:
            qr_payload = json.loads(qr_json)

            # Extract fields
            chunk = qr_payload['chunkNumber']
            totalChunks = qr_payload['totalChunks']
            name = qr_payload['name']
            data = qr_payload['data']

            LOGGER.debug('qr_file: %s', f)
            LOGGER.debug('\tname: %s', name)
            LOGGER.debug('\tchunk: %d/%d', chunk, totalChunks)

            # Haven't seen this file yet, so initialize a new structure
            # in `file_data`.
            if not name in file_data:
                b64_data = [None] * (totalChunks + 1)
                file_data[name] = {'name': name, 'data': b64_data}

            # Save data into structure
            file_data[name]['data'][chunk] = data

    # For each file we read in...
    for f_id, f_info in file_data.items():
        name = f_info['name']
        data = f_info['data']

        # Verify all chunks are present for the indicated file
        LOGGER.debug('Analyzing data for ID %s, name: %s', f_id, name)
        all_data_present = all(x is not None for x in data)
        if all_data_present:
            # All chunks present? Write back to file.
            LOGGER.debug('All data present for file: %s', name)
            complete_b64 = ''.join(data)
            b64_to_file(complete_b64, os.path.join(output_directory, name))
            print('Successfully decoded file: {f}'.format(f=name))
        else:
            # Compute missing data chunks
            missing_chunks = [i for i, e in enumerate(data) if e is None]
            print('Missing QR codes {mc} for file: {f}'.format(f=name, mc=missing_chunks))

def b64_to_file(b64_data, output_file):
    ''' Create a file from a base 64 string.

    Parameters:
      b64_data <string> The file encoded as a base 64 string.
      output_file <string> The location to save the decoded file.
    '''
    with open(output_file, 'wb') as f:
        file_data = b64decode(b64_data)
        f.write(file_data)
