#!/usr/bin/python
import os
import re
import subprocess

from setuptools import setup, find_packages

ROOT = "https://github.com/pprados/haystackapi"


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


# See setup.cfg

install_requirements = [
    'accept_types',
    'overrides',
    'tzlocal',
    'pytz',
    #    'hszinc',  # See dependency_links
    'pint',
    'click',
    'click_pathlib',
    'supersqlite',  # FIXME
]

requirements = install_requirements

dependency_links = ['git+https://github.com/pprados/hszinc.git@diff']  # FIXME
# dependency_links = ['git+https://github.com/pprados/hszinc.git#egg=ppr-4.0'], # FIXME

# Extra for a deployment in Flask server
flask_requirements = [
    'flask',
    'flask-cors'
]

# Extra for a deployment in AWS Lambda
lambda_requirements = [
                          'zappa'
                      ] + flask_requirements

azure_requirements = [
                         'azure-functions'
                     ] + flask_requirements

graphql_requirements = [
                           'graphene>=2.0',
                           'flask_graphql'
                       ] + flask_requirements

dev_requirements = [
    'python-dotenv',
    'zappa',
    'pytype',
    'ninja',
    'flake8',
    'pylint',
    'pytest',
    'twine',
    'mock',
    'supersqlite'
]

setup(name='haystackapi',
      url=_git_http_url(),
      setup_requires=['setuptools_scm'],
      use_scm_version=True,
      description='Implementation of Haystack REST API',
      long_description=open('README.md', mode='r', encoding='utf-8').read(),
      long_description_content_type='text/markdown',
      version="0.1",
      author='Philippe PRADOS',
      author_email='support@prados.fr',
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
      python_requires='>=3',
      extras_require={
          'dev': dev_requirements,
          'flask': flask_requirements,
          'graphql': graphql_requirements,
          'lambda': lambda_requirements,
          # 'azure': azure_requirements,
      },
      install_requires=install_requirements,
      requires=install_requirements,
      dependency_links=dependency_links,
      entry_points={
          "console_scripts": [
              'haystackapi = app.__init__:main'
          ]
      },
      project_urls={
          'Documentation': ROOT,
          'Source': ROOT,
          'Tracker': ROOT + '/issues',
      },
      )
