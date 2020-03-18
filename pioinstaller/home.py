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
import multiprocessing
import subprocess

import requests

from pioinstaller import exception

HTTP_HOST = "127.0.0.1"
HTTP_PORT_BEGIN = 8008
HTTP_PORT_END = 8050

log = logging.getLogger(__name__)


def _shutdown():
    for port in range(HTTP_PORT_BEGIN, HTTP_PORT_END):
        try:
            requests.get(
                "http://%s:%d?__shutdown__=1" % (HTTP_HOST, port), timeout=(0.5, 2)
            )
            log.debug("The server %s:%d is stopped", HTTP_HOST, port)
        except:  # pylint:disable=bare-except
            pass


def shutdown_pio_home_servers():
    proc = multiprocessing.Process(target=_shutdown)
    proc.start()
    proc.join(10)
    proc.terminate()
    return True


def install_pio_home(platformio_exe):
    try:
        subprocess.check_output(
            [platformio_exe, "home", "--host", "__do_not_start__"],
            stderr=subprocess.PIPE,
        )
        return True
    except Exception as e:  # pylint:disable=broad-except
        raise exception.PIOInstallerException("Could not install PIO Home: %s" % str(e))
