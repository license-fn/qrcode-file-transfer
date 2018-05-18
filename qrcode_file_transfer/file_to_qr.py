''' Contains utilities to convert files to QR codes.
'''
import json
import logging
import math
import os
import sys
import uuid
from base64 import b64encode

import qrcode

from .utils import confirm_dir

LOGGER = logging.getLogger(__name__)

# The number of bytes of file data allowed per QR code.
# The zbar parser can only handle so much data per QR code.
DATA_PER_CHUNK_BYTES = 625

def write_qr_code(output_file, data):
    ''' Writes the data to a QR code, which is saved to the indicated file as a PNG.

    Paramters:
      output_file <string> The file to save the QR code to, encoded as PNG.
      data <string> The data to encode into the QR code.
    '''
    img = qrcode.make(data)
    img.save(output_file)

def convert_file_to_qr(input_file, output_directory=''):
    ''' Converts the specified file to a series of QR code images.

    The images are saved in the output directory.

    Parameters:
      input_file <string> The file to convert to QR codes.
      output_directory <string> [Optional] The directory to save the generated QR codes to.
        This directory is created if it doesn't exist.
    '''
    # Try to create the output directory if it doesn't exist.
    if not confirm_dir(output_directory):
        LOGGER.warn('Failed to create output directory: %s', output_directory)
        return

    try:
        with open(input_file, 'rb') as f:
            # Read the file as binary and convert to b64
            data = f.read()

            b64_data = b64encode(data).decode('ascii')
            b64_data_len = len(b64_data)

            # Split into chunks.
            # This is required to keep QR codes to a parseable size.
            num_bytes = DATA_PER_CHUNK_BYTES
            num_chunks = math.ceil(len(b64_data) / num_bytes)
            input_file_name = os.path.basename(input_file)

            print('Encoding file {f}...'.format(f=input_file_name))
            LOGGER.debug('b64_data_len: %d', b64_data_len)
            LOGGER.debug('num_chunks: %d', num_chunks)
            LOGGER.debug('input_file_name: %s', input_file_name)

            # Write each chunk into a QR code
            for i in range(0, num_chunks):
                # Start and stop indicies of the b64 string for this chunk
                start_index = num_bytes * i
                end_index = num_bytes * (i + 1)

                LOGGER.debug('start_index: %d', start_index)
                LOGGER.debug('end_index: %d', end_index)

                # Construct payload to be placed into the QR code
                payload = { # len = 38 w/o name and data
                    'chunkNumber': i, # This chunk of the file
                    'totalChunks': num_chunks - 1, # Total chunks of the file
                    'name': input_file_name, # File name
                    'data': b64_data[start_index:end_index] # limit is ~650. Go 625 to be safe
                }
                # Dump to JSON with special separators to save space
                payload_json = json.dumps(payload, separators=(',',':'))
                LOGGER.debug('json dumps length {test}'.format(test=len(payload_json)))

                # Write QR code to file
                qr_file_name = '{file}_q{count}.png'.format(file=input_file_name, count=i)
                qr_file = os.path.join(output_directory, qr_file_name)
                LOGGER.debug('qr_file: %s', qr_file)

                write_qr_code(qr_file, payload_json)

            # Status msg
            print('Encoded file {f} in {n} QR codes.'.format(f=input_file_name, n=num_chunks))

    except OSError as e:
            print('Unable to read input file {f}. More info below:'.format(f=input_file))
            print('\t{e}'.format(e=e))
            return
