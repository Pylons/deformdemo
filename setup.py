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

# Standard Library
import os
import sys

from setuptools import find_packages
from setuptools import setup


here = os.path.abspath(os.path.dirname(__file__))

try:
    README = open(os.path.join(here, "README.rst")).read()
    CHANGES = open(os.path.join(here, "CHANGES.txt")).read()
except Exception:
    README = ""
    CHANGES = ""

PY3 = sys.version_info[0] == 3

requires = [
    "deform>=2.0dev",
    "pyramid>=1.5a1",  # route_name argument to resource_url
    "pyramid_chameleon",
    "pygments",
    "six",
    "waitress",
]

if not PY3:
    requires.extend(("Babel", "lingua"))

setupkw = dict(
    name="deformdemo",
    version="2.0.8.dev0",
    description="Demonstration application for Deform form library",
    long_description=README + "\n\n" + CHANGES,
    classifiers=[
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: Implementation :: CPython",
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
    extras_require={
        "lint": [
            "black",
            "check-manifest",
            "flake8",
            "flake8-bugbear",
            "flake8-builtins",
            "flake8-isort",
            "isort",
            "readme_renderer",
        ],
        "testing": ["nose", "nose-selecttests", "selenium>=3.0"],
    },
    entry_points="""\
    [paste.app_factory]
    demo = deformdemo:main
    mini = deformdemo.mini:main
    """,
    message_extractors={
        ".": [("**.py", "lingua_python", None), ("**.pt", "lingua_xml", None)]
    },
)

setup(**setupkw)
