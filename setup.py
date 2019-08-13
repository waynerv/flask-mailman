"""
    Flask-Mailman
    ~~~~~~~~~~~~~~
    Porting Django's email implementation to your Flask applications.

    :author: Xie Wei <ampedee@gmail.com>
    :copyright: (c) 2019 by Xie Wei.
    :license: BSD, see LICENSE for more details.
"""
from os import path

from setuptools import setup, find_packages

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='Flask-Mailman',
    version='0.1.5',
    description="Porting Django's email implementation to your Flask applications.",
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/waynerv/flask-mailman',
    license="BSD-3-Clause",
    author='Xie Wei',
    author_email='ampedee@gmail.com',
    keywords='flask mail smtp flask-mail',
    platforms='any',
    packages=find_packages(exclude=['docs', 'tests*']),
    python_requires='>=3.3',
    install_requires=['Flask>=0.10'],
    test_suite='nose.collector',
    tests_require=[
        'nose',
        'speaklater'
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Framework :: Django :: 2.2',
        'Framework :: Flask',
        'Topic :: Software Development :: Build Tools',
        'Topic :: Communications :: Email',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    project_urls={
        'Bug Reports': 'https://github.com/waynerv/flask-mailman/issues',
        'Source': 'https://github.com/waynerv/flask-mailman',
    },
)
