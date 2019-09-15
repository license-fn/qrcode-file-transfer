# qrcode-file-transfer
A Python package that can be used to transfer files with QR codes. Input a file, get QR code images. Print, email, or otherwise share your codes. Re-input these QR codes, get your original file back.

# Usage
This package is directly invokable as a module:
```
$ python3 -m qrcode_file_transfer <args>
```

In addition, the provided `setup.py` installs an alias that can be run directly from the command line:
```
$ qrcode_file_transfer <args>
```

## Arguments
```
usage: __main__.py [-h] [--output_dir OUTPUT_DIR]
                   {encode,decode} input_files [input_files ...]

Convert a file to a series of QR images and back again.

positional arguments:
  {encode,decode}       The mode of operation. Encode a file into QR code or
                        decode QR codes into files.
  input_files           The files to encode or the QR codes to decode.

optional arguments:
  -h, --help            show this help message and exit
  --output_dir OUTPUT_DIR
                        The output directory to write files to. Will be
                        created if it doesn't exist. (default: current working
                        dir)
```

## Example
The following command will encode the license and readme files into QR codes and save those images into a directory called `out`.
```
qrcode_file_transfer --output_dir=out encode LICENSE README.md
```

This will take the images generated in the previous command and convert them back into the original files. These files will be placed in the `out` directory.
```
qrcode_file_transfer --output_dir=out decode out/*.png
```

## Tips
* This is not intended to be used for large files.
* If possible, compress files before encoding into QR codes.

# Installation
## Requirements
* Python 3
* Encode
  * qrcode
  * Image
* Decode
  * Pillow
  * numpy
  * zbar-py

## From source
1. Clone the repository
2. Run `make install`
    * This command uses pip to install a wheel. If you are using a python virtual environment, be sure to activate it before installing.