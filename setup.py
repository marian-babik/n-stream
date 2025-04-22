from setuptools import setup
import nstream

NAME = 'nagios-stream'
VERSION = nstream.VERSION
DESCRIPTION = "Streaming support for Nagios"
LONG_DESCRIPTION = """
Streaming support for Nagios
"""
AUTHOR = nstream.AUTHOR
AUTHOR_EMAIL = nstream.AUTHOR_EMAIL
LICENSE = "ASL 2.0"
PLATFORMS = "Any"
URL = "https://gitlab.cern.ch/etf/n-stream"
CLASSIFIERS = [
    "Development Status :: 5 - Production/Stable",
    "License :: OSI Approved :: Apache Software License",
    "Operating System :: Unix",
    "Programming Language :: Python",
    "Programming Language :: Python :: 2.6",
    "Programming Language :: Python :: 2.7",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.0",
    "Programming Language :: Python :: 3.1",
    "Programming Language :: Python :: 3.2",
    "Programming Language :: Python :: 3.3",
    "Topic :: Software Development :: Libraries :: Python Modules"
]


setup(name=NAME,
      version=VERSION,
      description=DESCRIPTION,
      long_description=LONG_DESCRIPTION,
      author=AUTHOR,
      author_email=AUTHOR_EMAIL,
      license=LICENSE,
      platforms=PLATFORMS,
      url=URL,
      classifiers=CLASSIFIERS,
      keywords='operations nagios messaging queue ocsp',
      packages=['nstream', 'nstream.backends'],
      install_requires=['argparse', 'messaging', 'dirq'],
      data_files=[
          ('/etc/nstream', ['etc/nstream.cfg']),
          ('/etc/ncgx/templates/generic', ['etc/handlers.cfg']),
          ('/usr/bin', ['bin/enable_nstream', 'bin/disable_nstream', 'bin/ocsp_handler', 'bin/mq_handler']),
        ]
      )
