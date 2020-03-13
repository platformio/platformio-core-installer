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
import sys

import requests

from pioinstaller import core, exception, python, util

log = logging.getLogger(__name__)


VIRTUALENV_URL = "https://bootstrap.pypa.io/virtualenv/virtualenv.pyz"
PORTABLE_PYTHON_64 = (
    "https://dl.bintray.com/platformio/dl-misc/"
    "python-portable-windows_amd64-3.7.6.tar.gz"
)
PORTABLE_PYTHON_32 = (
    "https://dl.bintray.com/platformio/dl-misc/"
    "python-portable-windows_x86-3.7.6.tar.gz"
)


def get_penv_dir():
    if os.getenv("PLATFORMIO_PENV_DIR"):
        return os.getenv("PLATFORMIO_PENV_DIR")

    return os.path.join(core.get_core_dir(), "penv")


def get_penv_bin_dir():
    return os.path.join(get_penv_dir(), "Scripts" if util.IS_WINDOWS else "bin")


def clean_dir(penv_dir=None):
    penv_dir = penv_dir or get_penv_dir()
    log.debug("Virtualenv target path cleaning")
    try:
        return util.rmtree(penv_dir)
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


def download_portable_python():
    link = PORTABLE_PYTHON_64 if sys.maxsize > 2 ** 32 else PORTABLE_PYTHON_32

    archive_path = os.path.join(core.get_cache_dir(), "portable_python.tar.gz")
    util.download_file(link, archive_path)

    python_path = os.path.join(core.get_core_dir(), "python37")
    if os.path.isdir(python_path):
        try:
            util.rmtree(python_path)
        except:  # pylint: disable=bare-except
            pass
    try:
        os.makedirs(python_path)
    except:  # pylint:disable=bare-except
        pass

    return os.path.join(util.unpack_archive(archive_path, python_path), "python.exe")


def create_virtualenv_with_local(python_exe, penv_dir):
    venv_cmd_options = [
        [python_exe, "-m", "venv", penv_dir],
        [python_exe, "-m", "virtualenv", "-p", python_exe, penv_dir],
        ["virtualenv", "-p", python_exe, penv_dir],
        [python_exe, "-m", "virtualenv", penv_dir],
        ["virtualenv", penv_dir],
    ]
    last_error = None
    for command in venv_cmd_options:
        clean_dir(penv_dir)
        log.debug("Creating virtual environment: %s", " ".join(command))
        try:
            subprocess.check_output(command)
            return penv_dir
        except Exception as e:  # pylint:disable=broad-except
            last_error = e
    raise last_error  # pylint:disable=raising-bad-type


def create_virtualenv_with_download(python_exe, penv_dir):
    clean_dir(penv_dir)
    venv_path = download_virtualenv_script(core.get_cache_dir())
    if not venv_path:
        raise exception.PIOInstallerException("Could not find virtualenv script")
    command = [python_exe, venv_path, penv_dir]
    log.debug("Creating virtual environment: %s", " ".join(command))
    subprocess.check_output(command)
    return penv_dir


def create_virtualenv_with_portable_python(penv_dir):
    python_exe = download_portable_python()
    clean_dir(penv_dir)
    venv_path = download_virtualenv_script(core.get_cache_dir())
    if not venv_path:
        raise exception.PIOInstallerException("Could not find virtualenv script")
    command = [python_exe, venv_path, penv_dir]
    log.debug("Creating virtual environment: %s", " ".join(command))
    subprocess.check_output(command)
    return penv_dir


def create_virtualenv(penv_dir=None):
    penv_dir = penv_dir or get_penv_dir()

    log.info("Creating a virtual environment at %s", penv_dir)

    python_exes = python.find_compatible_pythons()
    for python_exe in python_exes:
        log.debug("Using %s Python for virtual environment.", python_exe)
        try:
            return create_virtualenv_with_local(python_exe, penv_dir)
        except Exception as e:  # pylint:disable=broad-except
            log.debug(
                "Could not create virtualenv with local packages"
                " Trying download virtualenv script and using it. Error: %s",
                str(e),
            )
            try:
                return create_virtualenv_with_download(python_exe, penv_dir)
            except Exception as e:  # pylint:disable=broad-except
                log.debug(
                    "Could not create virtualenv with downloaded script. Error: %s",
                    str(e),
                )

    if util.IS_WINDOWS and not python.is_portable():
        try:
            return create_virtualenv_with_portable_python(penv_dir)
        except Exception as e:  # pylint:disable=broad-except
            log.debug(
                "Could not create virtualenv with downloaded script. Error: %s", str(e),
            )
    raise exception.PIOInstallerException(
        "Could not create PIO Core Virtual Environment. "
        "Please create it manually -> http://bit.ly/pio-core-virtualenv"
    )
