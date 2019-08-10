"""
    Flask-Mailman
    ~~~~~~~~~~~~~~
    Porting Django's mail implementation to your Flask applications.

    :author: Xie Wei <ampedee@gmail.com>
    :copyright: (c) 2019 by Xie Wei.
    :license: BSD, see LICENSE for more details.
"""
from os import path

from setuptools import setup

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='Flask-Mailman',
    version='0.1.0',
    description="Porting Django's email implementation to your Flask applications.",
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/waynerv/flask-mailman',
    author='Xie Wei',
    author_email='ampedee@gmail.com',
    keywords='flask mail smtp flask-mail',
    packages=['flask_mailman'],
    python_requires='>=3.5',
    install_requires=['flask'],
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
