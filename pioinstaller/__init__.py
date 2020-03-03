# Copyright 2019-present PlatformIO Labs <contact@piolabs.com>

import logging.config
import os

VERSION = (0, 0, 0)
__version__ = ".".join([str(s) for s in VERSION])

__title__ = "platformio-installer"
__description__ = "An installer for PlatformIO Core"
__url__ = "https://piolabs.com"

__author__ = "PlatformIO Labs"
__email__ = "contact@piolabs.com"

__license__ = "Proprietary"
__copyright__ = "Copyright 2019-present PlatformIO Labs"

_config = None


# configure logging for packages
logging.basicConfig()

# setup time zone to UTC globally
os.environ["TZ"] = "+00:00"
try:
    from time import tzset

    tzset()
except ImportError:
    pass
