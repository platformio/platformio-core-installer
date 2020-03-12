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

import requests

from pioinstaller import core, exception, python, util

log = logging.getLogger(__name__)


VIRTUALENV_URL = "https://bootstrap.pypa.io/virtualenv/virtualenv.pyz"


def get_penv_dir():
    if os.getenv("PLATFORMIO_PENV_DIR"):
        return os.getenv("PLATFORMIO_PENV_DIR")

    return os.path.join(core.get_core_dir(), "penv")


def get_penv_bin_dir():
    return os.path.join(get_penv_dir(), "Scripts" if util.IS_WINDOWS else "bin")


def clean_penv_dir():
    log.debug("Virtualenv target path cleaning")
    try:
        return util.rmtree(get_penv_dir())
    except:  # pylint: disable=bare-except
        pass


def download_virtualenv_script(dst):
    venv_path = os.path.join(dst, "virtualenv.pyz")

    content_length = requests.head(VIRTUALENV_URL).headers.get("Content-Length")
    if os.path.exists(venv_path) and content_length == os.path.getsize(venv_path):
        log.debug("Virtualenv package archive already exists")
        return venv_path

    log.debug("Downloading virtualenv package archive")
    return util.download_file(VIRTUALENV_URL, venv_path)


def create_virtualenv_with_local(python_exe):
    penv_dir = get_penv_dir()
    venv_cmd_options = [
        [python_exe, "-m", "venv", penv_dir],
        [python_exe, "-m", "virtualenv", "-p", python_exe, penv_dir],
        ["virtualenv", "-p", python_exe, penv_dir],
        [python_exe, "-m", "virtualenv", penv_dir],
        ["virtualenv", penv_dir],
    ]
    last_error = None
    for command in venv_cmd_options:
        clean_penv_dir()
        log.debug("Creating virtual environment: %s", " ".join(command))
        try:
            subprocess.check_output(command)
            return penv_dir
        except Exception as e:  # pylint:disable=broad-except
            last_error = e
    raise last_error  # pylint:disable=raising-bad-type


def create_virtualenv_with_download(python_exe):
    clean_penv_dir()
    venv_path = download_virtualenv_script(core.get_cache_dir())
    if not venv_path:
        raise exception.PIOInstallerException("Could not find virtualenv script")
    command = [python_exe, venv_path, get_penv_dir()]
    log.debug("Creating virtual environment: %s", " ".join(command))
    subprocess.check_output(command)
    return get_penv_dir()


def create_virtualenv():
    log.info("Creating a virtual environment at %s", get_penv_dir())

    python_exes = python.find_compatible_pythons()
    for python_exe in python_exes:
        log.debug("Using %s Python for virtual environment.", python_exe)
        try:
            return create_virtualenv_with_local(python_exe)
        except Exception as e:  # pylint:disable=broad-except
            log.debug(
                "Could not create virtualenv with local packages"
                " Trying download virtualenv script and using it. Error: %s",
                str(e),
            )
            try:
                return create_virtualenv_with_download(python_exe)
            except Exception as e:  # pylint:disable=broad-except
                log.debug(
                    "Could not create virtualenv with downloaded script. Error: %s",
                    str(e),
                )
    raise exception.PIOInstallerException(
        "Could not create PIO Core Virtual Environment. "
        "Please create it manually -> http://bit.ly/pio-core-virtualenv"
    )
