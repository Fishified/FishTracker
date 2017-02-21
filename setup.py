# -*- coding: utf-8 -*-
"""
Created on Fri Feb 26 08:28:55 2016

@author: Jason
"""

from distutils.core import setup
import py2exe
import sys
import numpy
import pandas
sys.setrecursionlimit(5000)


import zmq.libzmq

setup(
    # ...
    zipfile='lib/library.zip',
    console=['Tracker.py'],
    options={
        'py2exe': {
            'includes': ['zmq.backend.cython'],
            'excludes': ['zmq.libzmq'],
            'dll_excludes': ['libzmq.pyd'],
        }
    },
    data_files=[
        ('lib', (zmq.libzmq.__file__,))
    ]
)



                 