# -*- coding: utf-8 -*-

# Learn more: https://github.com/kennethreitz/setup.py

from setuptools import setup, find_packages


with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='Commandline File UI',
    version='0.1.0',
    description='Navigate files from the command line',
    long_description=readme,
    author='Kenneth Reitz',
    author_email='kieran.jas.smith@gmail.com',
    url='https://kieransmith.in/projects/commandlinefileui',
    license=license,
    packages=find_packages('keyboard',exclude=('tests', 'docs'))
)
