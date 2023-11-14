##############################################################################
#
# Copyright (c) 2011 Agendaless Consulting and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the BSD-like license at
# http://www.repoze.org/LICENSE.txt.  A copy of the license should accompany
# this distribution.  THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL
# EXPRESS OR IMPLIED WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND
# FITNESS FOR A PARTICULAR PURPOSE
#
##############################################################################
from setuptools import find_packages
from setuptools import setup


def readfile(name):
    with open(name) as f:
        return f.read()


README = readfile("README.rst")
CHANGES = readfile("CHANGES.txt")
VERSION = '3.0.0.dev0'

requires = [
    "Babel",
    "deform >= 2.0.15.dev0",  # .dev0 allows pre-releases.
    "pyramid >= 2.0a0",  # route_name argument to resource_url
    "pyramid_chameleon",
    "pygments",
    "waitress",
]

lint_extras = [
    "black",
    "check-manifest",
    "flake8",
    "flake8-bugbear",
    "flake8-builtins",
    "isort",
    "readme_renderer",
]

testing_extras = ["flaky", "pytest"]

testing_extras.extend(["selenium >= 4.0.0.b4, < 4.9.0"])

setup(
    name="deformdemo",
    version=VERSION,
    description="Demonstration application for Deform form library",
    long_description=README + "\n\n" + CHANGES,
    classifiers=[
        "Development Status :: 6 - Mature",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: Repoze Public License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Topic :: Internet :: WWW/HTTP",
    ],
    keywords="web forms form generation schema validation deform",
    author="Chris McDonough, Agendaless Consulting",
    author_email="pylons-discuss@googlegroups.com",
    url="https://pylonsproject.org",
    license="BSD-derived (http://www.repoze.org/LICENSE.txt)",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=requires,
    extras_require={"lint": lint_extras, "testing": testing_extras},
    entry_points="""\
    [paste.app_factory]
    demo = deformdemo:main
    mini = deformdemo.mini:main
    """,
    message_extractors={
        ".": [("**.py", "lingua_python", None), ("**.pt", "lingua_xml", None)]
    },
)
