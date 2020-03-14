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

import json
import logging
import os
import platform
import subprocess
import time

import requests

from pioinstaller import __version__, core, exception, python, util

log = logging.getLogger(__name__)


VIRTUALENV_URL = "https://bootstrap.pypa.io/virtualenv/virtualenv.pyz"
PORTABLE_PYTHONS = {
    "windows_x86": "https://dl.bintray.com/platformio/dl-misc/"
    "python-portable-windows_x86-3.7.6.tar.gz",
    "windows_amd64": "https://dl.bintray.com/platformio/dl-misc/"
    "python-portable-windows_amd64-3.7.6.tar.gz",
}
PIP_URL = "https://bootstrap.pypa.io/get-pip.py"


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
    link = PORTABLE_PYTHONS.get(util.get_systype())

    archive_path = os.path.join(core.get_cache_dir(), "portable_python.tar.gz")
    log.debug("Downloading portable python...")
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

    if util.IS_WINDOWS:
        return os.path.join(
            util.unpack_archive(archive_path, python_path), "python.exe"
        )
    return os.path.join(util.unpack_archive(archive_path, python_path), "python")


def add_state_info(python_exe, penv_dir):
    output = subprocess.check_output([python_exe, "--version"]).decode()
    python_version = output.replace("Python ", "").replace("\n", "")
    json_info = {
        "created_on": int(round(time.time())),
        "python": {"path": python_exe, "version": python_version,},
        "installer_version": __version__,
        "platform": platform.platform(),
    }
    with open(os.path.join(penv_dir, "state.json"), "w") as fp:
        json.dump(json_info, fp)
    return os.path.join(penv_dir, "state.json")


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


def try_create_virtualenv_with_python_exe(python_exe, penv_dir):
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
                "Could not create virtualenv with downloaded script. Error: %s", str(e),
            )


def install_pip(penv_dir, python_exe):
    log.info("Updating Python package manager (PIP) in a virtual environment")
    try:
        log.debug("Creating pip.conf file in %s", penv_dir)
        with open(os.path.join(penv_dir, "pip.conf"), "w") as fp:
            fp.write("\n".join(["[global]", "user=no"]))

        log.debug("Downloading 'get-pip.py' installer...")
        get_pip_path = os.path.join(core.get_cache_dir(), os.path.basename(PIP_URL))
        util.download_file(PIP_URL, get_pip_path)

        log.debug("Installing pip")
        subprocess.check_output([python_exe, get_pip_path])
        log.info("PIP has been successfully updated!")
        return True
    except Exception as e:  # pylint:disable=broad-except
        log.debug(
            "Could not install pip. Error: %s", str(e),
        )
        return False


def create_virtualenv(penv_dir=None):
    penv_dir = penv_dir or get_penv_dir()

    log.info("Creating a virtual environment at %s", penv_dir)
    python_exe = None
    result_dir = None
    python_exes = python.find_compatible_pythons()
    for python_exe in python_exes:
        result_dir = try_create_virtualenv_with_python_exe(python_exe, penv_dir)
        if result_dir:
            break

    if (
        not result_dir
        and util.get_systype() in PORTABLE_PYTHONS
        and not python.is_portable()
    ):
        python_exe = download_portable_python()
        result_dir = try_create_virtualenv_with_python_exe(python_exe, penv_dir)

    if result_dir:
        add_state_info(python_exe, result_dir)
        log.info("Virtual environment has been successfully created!")
        python_exe = os.path.join(result_dir, "bin", "python")
        if util.IS_WINDOWS:
            python_exe = os.path.join(result_dir, "Scripts", "python.exe")
        install_pip(result_dir, python_exe)
        return python_exe

    raise exception.PIOInstallerException(
        "Could not create PIO Core Virtual Environment. "
        "Please create it manually -> http://bit.ly/pio-core-virtualenv"
    )
