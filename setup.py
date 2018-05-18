from setuptools import setup

setup(name='qrcode_file_transfer',
      version='0.0.1',
      description='Covert a file into QR codes and back again.',
      packages=['qrcode_file_transfer'],
      install_requires=['zbar-py', 'qrcode', 'Pillow', 'numpy'],
      entry_points={
          'console_scripts': ['qrcode_file_transfer = qrcode_file_transfer.__main__:main']
      }
     )
