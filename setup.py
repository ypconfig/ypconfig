#!/usr/bin/env python

from distutils.core import setup

setup(
    name='ypconfig',
    version='1.0',
    description='Tools required for ypconfig',
    author='Mark Schouten',
    author_email='mark@tuxis.nl',
    url='https://gitlab.tuxis.nl/mark/ypconfig',
    license='Closed',
    py_modules=['ypconfig.Config', 'ypconfig.Netlink'],
    package_dir={'': 'lib'},
    platforms=['linux'],
    data_files=[
    ]
)
