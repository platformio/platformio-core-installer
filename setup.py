# Copyright (c) 2014-present PlatformIO <contact@platformio.org>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


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
    long_description=open("README.rst").read(),
    author=__author__,
    author_email=__email__,
    url=__url__,
    license=__license__,
    install_requires=[
        # Core
        "click==8.0.4",  # >8.0.4 does not support Python 3.6
        "requests==2.27.1",
        "colorama==0.4.5",
        "semantic-version==2.8.5",  # >2.8.5 does not support Python 3.6
        "certifi==2022.12.7",
        # Misc
        "wheel==0.37.1",
    ],
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "pioinstaller = pioinstaller.__main__:main",
        ]
    },
)
