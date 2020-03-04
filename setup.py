# Copyright 2019-present PlatformIO Labs <contact@piolabs.com>

from pioinstaller import (
    __author__,
    __description__,
    __email__,
    __license__,
    __title__,
    __url__,
    __version__,
)
from setuptools import find_packages, setup

setup(
    name=__title__,
    version=__version__,
    description=__description__,
    long_description=open("README.md").read(),
    author=__author__,
    author_email=__email__,
    url=__url__,
    license=__license__,
    install_requires=[
        # Core
        "click==7.0",
    ],
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "pioinstaller = pioinstaller.cli:main",
        ]
    },
)
