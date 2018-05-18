from base64 import b64encode, b64decode
import json
import qrcode
import logging
import math
import numpy
import os
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

SCANNER = zbar.Scanner()

# The number of bytes of file data allowed per QR code.
# The zbar parser can only handle so much data per QR code.
DATA_PER_CHUNK_BYTES = 625

def read_qr_code(image_file):
    ''' Reads QR codes from the indicated image file and returns a list of data.

    Parameters:
      image_file <string> The image file to read.

    Returns:
      List<string> The string contained in each detected QR code.
    '''
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

    # Parse QR codes in the image
    res = SCANNER.scan(pix)

    # Extract data
    return [r.data for r in res]

def write_qr_code(output_file, data):
    ''' Writes the data to a QR code, which is saved to the indicated file as a PNG.

    Paramters:
      output_file <string> The file to save the QR code to, encoded as PNG.
      data <string> The data to encode into the QR code.
    '''
    img = qrcode.make(data)
    img.save(output_file)

def confirm_dir(dir):
    ''' Confirms that a directory can be written to.

    This function does the following:
      (1) If `dir` doesn't exist, to creates it.
      (2) If `dir` exists, checks that it is a directory.

    If this function returns True, then the directory exists.
    '''
    if not os.path.exists(dir):
        LOGGER.debug('Ouput directory doesn\'t exist! Creating.')
        try:
            os.makedirs(dir)
            return True
        except OSError as e:
            print('Unable to create output directory. More info below:')
            print('\t{e}'.format(e=e))
            return False
    elif not os.path.isdir(dir):
        print('Output directory already exists and is not a directory. ({d})'.format(d=dir))
        return False
    else:
        return True

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
                    'id': 0, # File ID
                    'chunkNumber': i, # This chunk of the file
                    'totalChunks': num_chunks - 1, # Total chunks of the file
                    'name': input_file_name, # File name
                    'data': b64_data[start_index:end_index] # limit is ~650. Go 625 to be safe
                }
                # Dump to JSON with special separators to save space
                payload_json = json.dumps(payload, separators=(',',':'))
                LOGGER.debug('json dumps length {test}'.format(test=len(payload_json)))

                # Write QR code to file
                qr_file_name = '{file}_q{count}.png'.format(file=input_file, count=i)
                qr_file = os.path.join(output_directory, qr_file_name)
                LOGGER.debug('qr_file: %s', qr_file)

                write_qr_code(qr_file, payload_json)
    except OSError as e:
        print('Unable to read input file {f}. More info below:'.format(f=input_file))
        print('\t{e}'.format(e=e))

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
    file_data = {} # FileID -> {name: fileName, data: Array of b64}
    for f in qr_files:
        # Read image and detect QR codes contained within
        qr_json_list = read_qr_code(f)
        LOGGER.debug('Found %d QR codes in file %s', len(qr_json_list), f)

        # For each QR found in the image
        for qr_json in qr_json_list:
            qr_payload = json.loads(qr_json)

            # Extract fields
            file_id = qr_payload['id']
            chunk = qr_payload['chunkNumber']
            totalChunks = qr_payload['totalChunks']
            name = qr_payload['name']
            data = qr_payload['data']

            LOGGER.debug('qr_file: %s', f)
            LOGGER.debug('\tid: %d', file_id)
            LOGGER.debug('\tchunk: %d/%d', chunk, totalChunks)
            LOGGER.debug('\tname: %s', name)

            # Haven't seen this file yet, so initialize a new structure
            # in `file_data`.
            if not file_id in file_data:
                b64_data = [None] * (totalChunks + 1)
                file_data[file_id] = {'name': name, 'data': b64_data}

            # Save data into structure
            file_data[file_id]['data'][chunk] = data

    # For each file we read in...
    for f_id, f_info in file_data.items():
        name = f_info['name']
        data = f_info['data']

        # Verify all chunks are present for the indicated file
        LOGGER.debug('Analyzing data for ID %d, name: %s', f_id, name)
        all_data_present = all(x is not None for x in data)
        if all_data_present:
            # All chunks present? Write back to file.
            LOGGER.debug('All data present for file: %s', name)
            complete_b64 = ''.join(data)
            b64_to_file(complete_b64, os.path.join(output_directory, name))
            print('Successfully decoded file: {f}'.format(f=name))
        else:
            LOGGER.warn('Missing data for file: %s', name)
            print('Missing data for file: {f}'.format(f=name))

def b64_to_file(b64_data, output_file):
    ''' Create a file from a base 64 string.

    Parameters:
      b64_data <string> The file encoded as a base 64 string.
      output_file <string> The location to save the decoded file.
    '''
    with open(output_file, 'wb') as f:
        file_data = b64decode(b64_data)
        f.write(file_data)

#convert_file_to_qr('LICENSE', 'license')
#reconstruct_files_from_qr(sys.argv[1:], 'license')