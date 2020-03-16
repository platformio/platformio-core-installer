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

import logging
import os

from pioinstaller import home, util

log = logging.getLogger(__name__)


def get_core_dir():
    if os.getenv("PLATFORMIO_CORE_DIR"):
        return os.getenv("PLATFORMIO_CORE_DIR")

    core_dir = os.path.join(util.expanduser("~"), ".platformio")
    if not util.IS_WINDOWS or not util.has_non_ascii_char(core_dir):
        return core_dir

    win_core_dir = os.path.splitdrive(core_dir)[0] + "\\.platformio"
    if not os.path.isdir(win_core_dir):
        try:
            os.makedirs(win_core_dir)
            with open(os.path.join(win_core_dir, "file.tmp"), "w") as fp:
                fp.write("test")
            os.remove(os.path.join(win_core_dir, "file.tmp"))
            return win_core_dir
        except:  # pylint:disable=bare-except
            pass

    return core_dir


def get_cache_dir(path=None):
    core_dir = path or get_core_dir()
    path = os.path.join(core_dir, ".cache")
    if not os.path.isdir(path):
        os.makedirs(path)
    return path


def install_platformio_core(shutdown_piohome=True):
    # pylint: disable=bad-option-value, import-outside-toplevel, unused-import, import-error, unused-variable, cyclic-import
    from pioinstaller import penv

    if shutdown_piohome:
        home.shutdown_pio_home_servers()

    penv.create_core_penv(get_core_dir())
