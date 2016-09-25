#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
from setuptools.command.test import test as TestCommand


class PyTest(TestCommand):

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.test_args)
        raise SystemExit(errno)


with open('README.md') as readme_file:
    readme = readme_file.read()


history = ''


install_requires_replacements = {
}

install_requires = list(set(
    install_requires_replacements.get(requirement.strip(), requirement.strip())
    for requirement in open('requirements.txt')
))

test_requirements = []

version = '0.0.1'  # preserve format, this is read from __init__.py

setup(
    name='rex',
    version=version,
    description="",
    long_description=readme + '\n\n' + history,
    author='ezmac',
    author_email='max@brainbot.com',
    url='https://github.com/ezmac/rex',
    packages=[
        'rex',
    ],
    include_package_data=True,
    license='BSD',
    zip_safe=False,
    keywords='rex',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.7',
    ],
    cmdclass={'test': PyTest},
    install_requires=install_requires,
    tests_require=test_requirements,
    entry_points='''
    [console_scripts]
    rex=rex.app:run
    '''
)