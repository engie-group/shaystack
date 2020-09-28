#!/usr/bin/python
import os
import re
import subprocess

from setuptools import setup, find_packages

# Return git remote url
def _git_url() -> str:
    try:
        with open(os.devnull, "wb") as devnull:
            out = subprocess.check_output(
                ["git", "remote", "get-url", "origin"],
                cwd=".",
                universal_newlines=True,
                stderr=devnull,
            )
        return out.strip()
    except subprocess.CalledProcessError:
        # git returned error, we are not in a git repo
        return ""
    except OSError:
        # git command not found, probably
        return ""


# Return Git remote in HTTP form
def _git_http_url() -> str:
    return re.sub(r".*@(.*):(.*).git", r"http://\1/\2", _git_url())


requirements = [
    'accept_types',
    'overrides',
    'tzlocal',

    'hszinc',
    'pint',
]

# Extra for a deployment in Flask server
flask_requirements = [
    'flask'
]

# Extra for a deployment in AWS Lambda
lambda_requirements = [
    'zappa'
] + flask_requirements

dev_requirements = [
    'python-dotenv',
    'zappa',
    'pytype',
    'ninja',
    'flake8',
    'pylint',
    'pytest',
]

setup(name='haystackapi',
      url=_git_http_url(),
      description='Implementation of Haystack REST API',
      version="0.1",
      author='Philippe PRADOS',
      # author_email='support@prados.fr',
      license='Apache v2',
      zip_safe=False,
      packages=find_packages(),
      include_package_data=True,
      classifiers=[
          'Development Status :: 4 - Beta',
          'Environment :: Web Environment',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: Apache Software License',
          'Programming Language :: Python',
          'Programming Language :: Python :: 3.8',
          'Topic :: Scientific/Engineering',
          'Topic :: Scientific/Engineering :: Information Analysis',
      ],
      requires=requirements,
      extras_require={
          'dev': dev_requirements,
          'flask': flask_requirements,
          'lambda': lambda_requirements,
          # TODO 'test': test_requirements,
      },
      install_requires=requirements,
      entry_points={
          "console_scripts": [
              'haystackapi-run = app.__init__:main'
          ]
      },
      )
