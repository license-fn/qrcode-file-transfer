"""Serves as an entry point for the qrcode_file_transfer modile.

Contains logic for running the package as an application.
"""
import argparse
import logging
import sys

from .file_to_qr import convert_file_to_qr
from .qr_to_file import reconstruct_files_from_qr

LOGGER = logging.getLogger(__name__)

def main():
    """ The entry point of the package when run as a command line application.
    """
    parser = argparse.ArgumentParser(
        description=('Convert a file to a series of QR images and back again.'))
    parser.add_argument('mode', choices=['encode','decode'],
        help='The mode of operation. Encode a file into QR code or decode QR codes into files.')
    parser.add_argument('--output_dir', default='',
        help=('The output directory to write files to. Will be created if it '
              'doesn\'t exist. (default: current working dir)'))
    parser.add_argument('input_files', nargs='+', default=[],
        help='The files to encode or the QR codes to decode.')

    # Pull out args
    args = parser.parse_args()
    mode = args.mode
    output_dir = args.output_dir
    input_files = args.input_files
    LOGGER.debug('mode = %s', mode)
    LOGGER.debug('output_dir = %s', output_dir)
    LOGGER.debug('input_files = %s', input_files)

    if mode == 'encode':
        for f in input_files:
            LOGGER.debug('Encoding %s...', f)
            convert_file_to_qr(f, output_dir)
            LOGGER.debug('Done')
    elif mode == 'decode':
        LOGGER.debug('Decoding')
        reconstruct_files_from_qr(input_files, output_dir)
        LOGGER.debug('Done!')

main()
