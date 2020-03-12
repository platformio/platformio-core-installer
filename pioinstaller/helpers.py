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
import os
import subprocess
import tarfile

import requests

from pioinstaller import core, exception, python, util

HTTP_HOST = "127.0.0.1"
HTTP_PORT_BEGIN = 8008
HTTP_PORT_END = 8050

log = logging.getLogger(__name__)

VIRTUALENV_URL = (
    "https://files.pythonhosted.org/packages/"
    "e7/80/15d28e5a075fb02366ce97558120bb987868dab3600233ec7be032dc6d01/virtualenv-16.7.7.tar.gz"
)

TMP_PATH = "/tmp/pioinstaller/venv"


def shutdown_pio_home_servers():
    def _shutdown():
        for port in range(HTTP_PORT_BEGIN, HTTP_PORT_END):
            try:
                requests.get(
                    "http://%s:%d?__shutdown__=1" % (HTTP_HOST, port), timeout=(0.5, 2)
                )
                log.debug("The server %s:%d is stopped", HTTP_HOST, port)
            except:  # pylint:disable=bare-except
                pass

    proc = multiprocessing.Process(target=_shutdown)
    proc.start()
    proc.join(10)
    proc.terminate()
    return True


def download_virtualenv_exe():
    archive_path = os.path.join(TMP_PATH, "virtualenv.tar.gz")

    content_length = requests.head(VIRTUALENV_URL).headers.get("Content-Length")
    if os.path.exists(archive_path) and content_length == os.stat(archive_path).st_size:
        log.debug("Virtualenv package archive already exists.")
        venv_path = util.find_file("virtualenv.py", TMP_PATH)
        if venv_path:
            log.debug("Virtualenv script file already exists")
            return venv_path

    log.debug("Downloading virtualenv package archive")
    with open(archive_path, "wb") as fp:
        fp.write(requests.get(VIRTUALENV_URL).content)

    log.debug("Unpacking virtualenv package")
    with tarfile.open(archive_path, "r:gz") as fp:
        fp.extractall(TMP_PATH)

    return util.find_file("virtualenv.py", TMP_PATH)


def create_virtualenv_with_local(python_exe):
    venv_cmd_options = [
        [python_exe, "-m", "venv", core.get_penv_dir()],
        [python_exe, "-m", "virtualenv", "-p", python_exe, core.get_penv_dir()],
        ["virtualenv", "-p", python_exe, core.get_penv_dir()],
        [python_exe, "-m", "virtualenv", core.get_penv_dir()],
        ["virtualenv", core.get_penv_dir()],
    ]
    last_error = None
    for command in venv_cmd_options:
        core.clean_penv_dir()
        log.debug("Running command: %s", " ".join(command))
        try:
            subprocess.check_output(command)
            return core.get_penv_dir()
        except Exception as e:  # pylint:disable=broad-except
            last_error = e
    raise last_error  # pylint:disable=raising-bad-type


def create_virtualenv_with_download(python_exe):
    core.clean_penv_dir()
    venv_path = download_virtualenv_exe()
    if not venv_path:
        raise exception.PIOInstallerException("Can not find virtualenv.py script.")
    command = [python_exe, venv_path, core.get_penv_dir()]
    log.debug("Running command: %s", " ".join(command))
    subprocess.check_output(command)
    return core.get_penv_dir()


def create_pio_virtualenv():
    log.info("Creating virtualenv.")
    log.info("Virtualenv target path: %s.", core.get_penv_dir())

    log.debug("Creating temporary dir: %s.", TMP_PATH)
    util.create_dir(TMP_PATH)

    python_exes = python.find_compatible_pythons()
    penv_path = None
    for python_exe in python_exes:
        log.debug("Using %s for virtualenv creating", python_exe)
        try:
            penv_path = create_virtualenv_with_local(python_exe)
            break
        except Exception as e:  # pylint:disable=broad-except
            log.debug(
                "Can not create virtualenv with local packages."
                " Trying download virtualenv.py script and using it. Error: %s",
                str(e),
            )
            try:
                penv_path = create_virtualenv_with_download(python_exe)
                break
            except Exception as e:  # pylint:disable=broad-except
                log.debug(
                    "Can not create virtualenv with downloaded script. Error: %s",
                    str(e),
                )

    log.debug("Removing temporary dir.")
    util.rmtree(TMP_PATH)

    if penv_path:
        log.info("Virtualenv successfully created.")
        return penv_path
    raise exception.PIOInstallerException(
        "Could not create PIO Core Virtual Environment. "
        "Please create it manually -> http://bit.ly/pio-core-virtualenv"
    )
