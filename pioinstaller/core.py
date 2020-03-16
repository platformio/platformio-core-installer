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
import subprocess

from pioinstaller import exception, home, util

log = logging.getLogger(__name__)

PIO_CORE_DEVELOP_URL = "https://github.com/platformio/platformio/archive/develop.zip"


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


def install_platformio_core(shutdown_piohome=True, develop=False):
    # pylint: disable=bad-option-value, import-outside-toplevel, unused-import, import-error, unused-variable, cyclic-import
    from pioinstaller import penv

    if shutdown_piohome:
        home.shutdown_pio_home_servers()

    penv_dir = penv.create_core_penv()
    python_exe = os.path.join(
        penv.get_penv_bin_dir(penv_dir), "python.exe" if util.IS_WINDOWS else "python"
    )
    command = [python_exe, "-m", "pip", "install", "-U"]
    if develop:
        log.info("Installing a development version of PlatformIO Core")
        command.append(PIO_CORE_DEVELOP_URL)
    else:
        log.info("Installing PlatformIO Core")
        command.append("platformio")
    try:
        subprocess.check_output(command)
    except Exception as e:  # pylint:disable=broad-except
        error = str(e)
        if util.IS_WINDOWS:
            error = (
                "If you have antivirus/firewall/defender software in a system,"
                " try to disable it for a while.\n %s" % error
            )
        raise exception.PIOInstallerException(
            "Could not install PlatformIO Core: %s" % error
        )
    platformio_exe = os.path.join(
        penv.get_penv_bin_dir(penv_dir),
        "platformio.exe" if util.IS_WINDOWS else "platformio",
    )
    try:
        home.install_pio_home(platformio_exe)
    except Exception as e:  # pylint:disable=broad-except
        log.debug(e)
    log.info("PlatformIO Core has been successfully installed!")
    return True
