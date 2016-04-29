#!/usr/bin/python
from setuptools import setup
import sys
from hszinc import __version__

setup (name = 'hszinc',
        version = __version__,
        packages = [
            'hszinc',
        ],
        requires = [
            'parsimonious',
            'pytz',
            'iso8601',
            'six',
        ],
        install_requires = [
            'parsimonious',
            'pytz',
            'iso8601',
            'six',
        ]
)
