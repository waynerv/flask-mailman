# Flask-Mailman

![PyPI](https://img.shields.io/pypi/v/flask-mailman?color=blue)
![PyPI - Downloads](https://img.shields.io/pypi/dm/flask-mailman?color=brightgreen)
[![dev workflow](https://github.com/waynerv/flask-mailman/actions/workflows/dev.yml/badge.svg?branch=master)](https://github.com/waynerv/flask-mailman/actions/workflows/dev.yml)
![GitHub commits since latest release (by SemVer)](https://img.shields.io/github/commits-since/waynerv/flask-mailman/latest?color=cyan)
![PyPI - License](https://img.shields.io/pypi/l/flask-mailman?color=blue)

Flask-Mailman is a Flask extension providing simple email sending capabilities.

It was meant to replace unmaintained Flask-Mail with a better warranty and more features.

## Usage

Flask-Mail ported Django's email implementation to your Flask applications, which may be the best mail sending implementation that's available for python.

The way of using this extension is almost the same as Django.

Documentation: https://waynerv.github.io/flask-mailman.

**Note: A few breaking changes have been made in v0.2.0 version** to ensure that API of this extension is basically the same as Django.
Users migrating from Flask-Mail should upgrade with caution.

## Credits

Thanks to [Jetbrains](https://jb.gg/OpenSource) for providing an Open Source license for this project.

[![Jetbrains Logo](docs/img/jetbrains-variant-4.png)](www.jetbrains.com)

Build tools and workflows of this project was inspired by [waynerv/cookiecutter-pypackage](https://github.com/waynerv/cookiecutter-pypackage) project template.
