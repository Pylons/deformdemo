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

import os
import sys

from setuptools import setup
from setuptools import find_packages

here = os.path.abspath(os.path.dirname(__file__))

try:
    README = open(os.path.join(here, 'README.rst')).read()
    CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()
except:
    README = ''
    CHANGES = ''

PY3 = sys.version_info[0] == 3

requires = ['deform>=2.0dev',
            'pyramid>=1.5a1', # route_name argument to resource_url
            'pyramid_chameleon',
            'pygments',
            'waitress']

testing_extras = ['webtest',]

if not PY3:
    requires.extend((
            'Babel',
            'lingua',
            ))

setupkw = dict(
    name='deformdemo',
    version='0.0',
    description='Demonstration application for Deform form library',
    long_description=README + '\n\n' + CHANGES,
    classifiers=[
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        ],
    keywords='web forms form generation schema validation',
    author="Chris McDonough, Agendaless Consulting",
    author_email="pylons-discuss@googlegroups.com",
    url="http://pylonsproject.org",
    license="BSD-derived (http://www.repoze.org/LICENSE.txt)",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    tests_require=testing_extras,
    install_requires=requires,
    extras_require = {
        'testing': ['nose', 'selenium'],
    },
    entry_points = """\
    [paste.app_factory]
    demo = deformdemo:main
    """,
    message_extractors = { '.': [
        ('**.py',   'lingua_python', None ),
        ('**.pt',   'lingua_xml', None ),
        ]},
    )

setup(**setupkw)
