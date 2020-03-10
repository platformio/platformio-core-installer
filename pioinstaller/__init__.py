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

import logging.config

VERSION = (0, 1, 0)
__version__ = ".".join([str(s) for s in VERSION])

__title__ = "platformio-installer"
__description__ = "An installer for PlatformIO Core"

__url__ = "https://platformio.org"

__author__ = "PlatformIO"
__email__ = "contact@platformio.org"

__license__ = "Apache Software License"
__copyright__ = "Copyright 2014-present PlatformIO"


logging.basicConfig()
logging.config.dictConfig(
    {"version": 1, "loggers": {"pioinstaller": {"level": "INFO"}}}
)
