#!/usr/bin/python
import os
import subprocess

import setuptools

ROOT = "https://github.com/pprados/haystackapi"

import re

# PPR: Use https://docs.openstack.org/pbr/latest
DEFAULT_VERSION = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                            open("haystackapi/_version.py", "rt").read(),
                            re.M).group(1)


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
    'pyparsing',
    'pytz',
    'iso8601',
    'six',
    'accept_types',
    'overrides',
    'tzlocal',
    'pint',
    'click',
    'click_pathlib',
]

requirements = install_requirements

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
    'nose',
    'twine',
    'mock',
    'nose',
    'coverage',
    'psycopg2',
    'supersqlite',
    'sphinx', 'sphinx-execute-code', 'sphinx_rtd_theme', 'recommonmark', 'sphinx-markdown-tables',  # To generate doc
]

setuptools.setup(
    pbr=True
)

# setup(setup_requires=['pbr'],
#       pbr=True,
# # #      use_scm_version=True,
# # #      description='Implementation of Haystack Project Specification',
# # #      long_description=open('README.md', mode='r', encoding='utf-8').read(),
# # #      long_description_content_type='text/markdown',
# # #      version=DEFAULT_VERSION,
# # #      author='Philippe PRADOS',
# # #      author_email='support@prados.fr',
# # #      license='Apache v2',
# #       zip_safe=False,
# #       packages=find_packages(),
# #       include_package_data=True,
# #       classifiers=[
# #           'Development Status :: 4 - Beta',
# #           'Environment :: Web Environment',
# #           'Intended Audience :: Developers',
# #           'License :: OSI Approved :: BSD License',
# #           'Programming Language :: Python',
# #           'Programming Language :: Python :: 3.7',
# #           'Programming Language :: Python :: 3.8',
# #           'Programming Language :: Python :: 3.9',
# #           'Topic :: Scientific/Engineering',
# #           'Topic :: Scientific/Engineering :: Information Analysis',
# #           'Topic :: Software Development :: Libraries :: Python Modules',
# #       ],
# #       python_requires='>=3',
#       extras_require={
#           'dev': dev_requirements,
#           'flask': flask_requirements,
#           'graphql': graphql_requirements,
#           'lambda': lambda_requirements,
#           # 'azure': azure_requirements,
#       },
#       install_requires=install_requirements,
#       requires=install_requirements,
# #       entry_points={
# #           "console_scripts": [
# #               'haystackapi = app.__init__:main',
# #               'haystackapi_import_db = haystackapi.providers.import_db:main',
# #               'haystackapi_import_s3 = haystackapi.providers.import_s3:main',
# #           ]
# #       },
# #       project_urls={
# #           'Documentation': ROOT,
# #           'Source': ROOT,
# #           'Tracker': ROOT + '/issues',
# #       },
#       )
