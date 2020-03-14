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


def download_portable_python():
    log.debug("Trying download portable python")
    link = PORTABLE_PYTHONS.get(util.get_systype())
    if not link:
        return None
    try:
        log.debug("Downloading portable python...")
        archive_path = util.download_file(
            link, os.path.join(core.get_cache_dir(), os.path.basename(link))
        )

        python_path = os.path.join(core.get_core_dir(), "python37")
        util.safe_clean_dir(python_path)
        util.safe_create_dir(python_path, raise_exception=True)

        log.debug("Unpacking portable python...")
        util.unpack_archive(archive_path, python_path)
        if util.IS_WINDOWS:
            return os.path.join(python_path, "python.exe")
        return os.path.join(python_path, "python")
    except:  # pylint:disable=bare-except
        log.debug("Could not download portable python")


def add_state_info(python_exe, penv_dir):
    version_code = (
        "import sys; version=sys.version_info; "
        "print('%d.%d.%d'%(version[0],version[1],version[2]))"
    )
    python_version = (
        subprocess.check_output([python_exe, "-c", version_code])
        .decode()
        .replace("\n", "")
    )
    json_info = {
        "created_on": int(round(time.time())),
        "python": {"path": python_exe, "version": python_version,},
        "installer_version": __version__,
        "platform": platform.platform(),
    }
    with open(os.path.join(penv_dir, "state.json"), "w") as fp:
        json.dump(json_info, fp)
    return os.path.join(penv_dir, "state.json")


def create_virtualenv_with_local_scripts(python_exe, penv_dir):
    venv_cmd_options = [
        [python_exe, "-m", "venv", penv_dir],
        [python_exe, "-m", "virtualenv", "-p", python_exe, penv_dir],
        ["virtualenv", "-p", python_exe, penv_dir],
        [python_exe, "-m", "virtualenv", penv_dir],
        ["virtualenv", penv_dir],
    ]
    last_error = None
    for command in venv_cmd_options:
        util.safe_clean_dir(penv_dir)
        log.debug("Creating virtual environment: %s", " ".join(command))
        try:
            subprocess.check_output(command)
            return penv_dir
        except Exception as e:  # pylint:disable=broad-except
            last_error = e
    raise last_error  # pylint:disable=raising-bad-type


def create_virtualenv_with_external_script(python_exe, penv_dir):
    util.safe_clean_dir(penv_dir)

    log.debug("Downloading virtualenv package archive")
    venv_script_path = util.download_file(
        VIRTUALENV_URL,
        os.path.join(core.get_cache_dir(), os.path.basename(VIRTUALENV_URL)),
    )
    if not venv_script_path:
        raise exception.PIOInstallerException("Could not find virtualenv script")
    command = [python_exe, venv_script_path, penv_dir]
    log.debug("Creating virtual environment: %s", " ".join(command))
    subprocess.check_output(command)
    return penv_dir


def create_virtualenv_with_python_executable(python_exe, penv_dir):
    log.debug("Using %s Python for virtual environment.", python_exe)
    try:
        return create_virtualenv_with_local_scripts(python_exe, penv_dir)
    except Exception as e:  # pylint:disable=broad-except
        log.debug(
            "Could not create virtualenv with local packages"
            " Trying download virtualenv script and using it. Error: %s",
            str(e),
        )
        try:
            return create_virtualenv_with_external_script(python_exe, penv_dir)
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
    for python_exe in python.find_compatible_pythons():
        result_dir = create_virtualenv_with_python_executable(python_exe, penv_dir)
        if result_dir:
            break

    if (
        not result_dir
        and util.get_systype() in PORTABLE_PYTHONS
        and not python.is_portable()
    ):
        python_exe = download_portable_python()
        if python_exe:
            result_dir = create_virtualenv_with_python_executable(python_exe, penv_dir)

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
