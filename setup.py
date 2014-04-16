#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

import dragonmasher


if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    sys.exit()

def open_file(filename):
    """Open and read the file *filename*."""
    with open(filename) as f:
        return f.read()

readme = open_file('README.rst')
history = open_file('HISTORY.rst').replace('.. :changelog:', '')

setup(
    name='Dragon Masher',
    version=dragonmasher.__version__,
    description='Dragon Masher provides access to Chinese word/character data',
    long_description=readme + '\n\n' + history,
    author='Thomas Roten',
    author_email='thomas@roten.us',
    url='https://github.com/tsroten/dragonmasher',
    packages=['dragonmasher'],
    package_dir={'dragonmasher': 'dragonmasher'},
    include_package_data=True,
    package_data={'dragonmasher': ['data/*.csv']},
    install_requires=[
        'zhon>=1.0',
        'ticktock>=0.1.2',
        'fcache>=0.4.4',
        'dragonmapper'
    ],
    license='BSD',
    keywords=['dragonmasher', 'chinese', 'data', 'hsk', 'cedict', 'cc-cedict',
              'tocfl', 'unihan', 'junda'],
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],
    test_suite='dragonmasher.tests',
)
