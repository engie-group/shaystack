#!/usr/bin/python
from setuptools import setup
import sys
sys.path.insert(0, 'src')
from hszinc import __version__

setup (name = 'hszinc',
	package_dir = {'': 'src'},
        version = __version__,
	packages = [
            'hszinc',
        ],
)
