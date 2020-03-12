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
import tempfile

import requests

from pioinstaller import core, exception, python, util

log = logging.getLogger(__name__)


VIRTUALENV_URL = (
    "https://files.pythonhosted.org/packages/"
    "e7/80/15d28e5a075fb02366ce97558120bb987868dab3600233ec7be032dc6d01/virtualenv-16.7.7.tar.gz"
)


def get_penv_dir():
    if os.getenv("PLATFORMIO_PENV_DIR"):
        return os.getenv("PLATFORMIO_PENV_DIR")

    return os.path.join(core.get_core_dir(), "penv")


def get_penv_bin_dir():
    return os.path.join(get_penv_dir(), "Scripts" if util.IS_WINDOWS else "bin")


def clean_penv_dir():
    log.debug("Virtualenv target path cleaning.")
    try:
        return util.rmtree(get_penv_dir())
    except:  # pylint: disable=bare-except
        pass


def download_virtualenv_exe(tmp_dir):
    archive_path = os.path.join(tmp_dir, "virtualenv.tar.gz")

    content_length = requests.head(VIRTUALENV_URL).headers.get("Content-Length")
    if os.path.exists(archive_path) and content_length == os.path.getsize(archive_path):
        log.debug("Virtualenv package archive already exists.")
        venv_path = util.find_file("virtualenv.py", tmp_dir)
        if venv_path:
            log.debug("Virtualenv script file already exists")
            return venv_path

    log.debug("Downloading virtualenv package archive")
    util.download_file(VIRTUALENV_URL, archive_path)

    log.debug("Unpacking virtualenv package")
    util.unpack_archive(archive_path, tmp_dir)

    return util.find_file("virtualenv.py", tmp_dir)


def create_virtualenv_with_local(python_exe):
    venv_cmd_options = [
        [python_exe, "-m", "venv", get_penv_dir()],
        [python_exe, "-m", "virtualenv", "-p", python_exe, get_penv_dir()],
        ["virtualenv", "-p", python_exe, get_penv_dir()],
        [python_exe, "-m", "virtualenv", get_penv_dir()],
        ["virtualenv", get_penv_dir()],
    ]
    last_error = None
    for command in venv_cmd_options:
        clean_penv_dir()
        log.debug("Running command: %s", " ".join(command))
        try:
            subprocess.check_output(command)
            return get_penv_dir()
        except Exception as e:  # pylint:disable=broad-except
            last_error = e
    raise last_error  # pylint:disable=raising-bad-type


def create_virtualenv_with_download(python_exe, tmp_dir):
    clean_penv_dir()
    venv_path = download_virtualenv_exe(tmp_dir)
    if not venv_path:
        raise exception.PIOInstallerException("Can not find virtualenv.py script.")
    command = [python_exe, venv_path, get_penv_dir()]
    log.debug("Running command: %s", " ".join(command))
    subprocess.check_output(command)
    return get_penv_dir()


def create_virtualenv():
    log.info("Creating virtualenv.")
    log.info("Virtualenv target path: %s.", get_penv_dir())

    log.debug("Creating temporary dir:")
    tmp_dir = tempfile.mkdtemp()
    log.debug(tmp_dir)
    try:
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
                    penv_path = create_virtualenv_with_download(python_exe, tmp_dir)
                    break
                except Exception as e:  # pylint:disable=broad-except
                    log.debug(
                        "Can not create virtualenv with downloaded script. Error: %s",
                        str(e),
                    )

        if penv_path:
            log.info("Virtualenv successfully created.")
            return penv_path
        raise exception.PIOInstallerException(
            "Could not create PIO Core Virtual Environment. "
            "Please create it manually -> http://bit.ly/pio-core-virtualenv"
        )
    finally:
        util.rmtree(tmp_dir)
