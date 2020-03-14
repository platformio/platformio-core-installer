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

from pioinstaller import __version__, exception, python, util

log = logging.getLogger(__name__)


VIRTUALENV_URL = "https://bootstrap.pypa.io/virtualenv/virtualenv.pyz"

PIP_URL = "https://bootstrap.pypa.io/get-pip.py"


class VirtualEnviroment(object):
    def __init__(self, core_dir, penv_dir, cache_dir, python_exe=None):
        self.core_dir = core_dir
        self.penv_dir = penv_dir
        self.cache_dir = cache_dir
        self.python_exe = python_exe
        self.result_dir = None

    def create_with_local_scripts(self):
        if not self.python_exe:
            raise exception.PIOInstallerException("Python executable is not set")
        venv_cmd_options = [
            [self.python_exe, "-m", "venv", self.penv_dir],
            [self.python_exe, "-m", "virtualenv", "-p", self.python_exe, self.penv_dir],
            ["virtualenv", "-p", self.python_exe, self.penv_dir],
            [self.python_exe, "-m", "virtualenv", self.penv_dir],
            ["virtualenv", self.penv_dir],
        ]
        last_error = None
        for command in venv_cmd_options:
            util.safe_clean_dir(self.penv_dir)
            log.debug("Creating virtual environment: %s", " ".join(command))
            try:
                subprocess.check_output(command)
                return self.penv_dir
            except Exception as e:  # pylint:disable=broad-except
                last_error = e
        raise last_error  # pylint:disable=raising-bad-type

    def create_with_external_script(self):
        if not self.python_exe:
            raise exception.PIOInstallerException("Python executable is not set")
        util.safe_clean_dir(self.penv_dir)

        log.debug("Downloading virtualenv package archive")
        venv_script_path = util.download_file(
            VIRTUALENV_URL,
            os.path.join(self.cache_dir, os.path.basename(VIRTUALENV_URL)),
        )
        if not venv_script_path:
            raise exception.PIOInstallerException("Could not find virtualenv script")
        command = [self.python_exe, venv_script_path, self.penv_dir]
        log.debug("Creating virtual environment: %s", " ".join(command))
        subprocess.check_output(command)
        return self.penv_dir

    def try_create_with_current_python_exe(self):
        if not self.python_exe:
            raise exception.PIOInstallerException("Python executable is not set")
        log.debug("Using %s Python for virtual environment.", self.python_exe)
        try:
            return self.create_with_local_scripts()
        except Exception as e:  # pylint:disable=broad-except
            log.debug(
                "Could not create virtualenv with local packages"
                " Trying download virtualenv script and using it. Error: %s",
                str(e),
            )
            try:
                return self.create_with_external_script()
            except Exception as e:  # pylint:disable=broad-except
                log.debug(
                    "Could not create virtualenv with downloaded script. Error: %s",
                    str(e),
                )

    def add_state_info(self):
        if not self.python_exe:
            raise exception.PIOInstallerException("Python executable is not set")
        version_code = (
            "import sys; version=sys.version_info; "
            "print('%d.%d.%d'%(version[0],version[1],version[2]))"
        )
        python_version = (
            subprocess.check_output([self.python_exe, "-c", version_code])
            .decode()
            .replace("\n", "")
        )
        json_info = {
            "created_on": int(round(time.time())),
            "python": {"path": self.python_exe, "version": python_version,},
            "installer_version": __version__,
            "platform": platform.platform(),
        }
        with open(os.path.join(self.penv_dir, "state.json"), "w") as fp:
            json.dump(json_info, fp)
        return os.path.join(self.penv_dir, "state.json")

    def install_pip(self):
        if not self.python_exe:
            raise exception.PIOInstallerException("Python executable is not set")
        log.info("Updating Python package manager (PIP) in a virtual environment")
        try:
            log.debug("Creating pip.conf file in %s", self.penv_dir)
            with open(os.path.join(self.penv_dir, "pip.conf"), "w") as fp:
                fp.write("\n".join(["[global]", "user=no"]))

            log.debug("Downloading 'get-pip.py' installer...")
            get_pip_path = os.path.join(self.cache_dir, os.path.basename(PIP_URL))
            util.download_file(PIP_URL, get_pip_path)

            log.debug("Installing pip")
            subprocess.check_output([self.python_exe, get_pip_path])
            log.info("PIP has been successfully updated!")
            return True
        except Exception as e:  # pylint:disable=broad-except
            log.debug(
                "Could not install pip. Error: %s", str(e),
            )
            return False

    def create(self):
        log.info("Creating a virtual environment at %s", self.penv_dir)

        for self.python_exe in python.find_compatible_pythons():
            self.result_dir = self.try_create_with_current_python_exe()
            if self.result_dir:
                break

        if (
            not self.result_dir
            and util.get_systype() in python.PORTABLE_PYTHONS
            and not python.is_portable()
        ):
            self.python_exe = python.download_portable(
                core_dir=self.core_dir, cache_dir=self.cache_dir
            )
            if self.python_exe:
                self.result_dir = self.try_create_with_current_python_exe()

        if self.result_dir:
            self.penv_dir = self.result_dir

            self.add_state_info()
            log.info("Virtual environment has been successfully created!")
            self.python_exe = os.path.join(self.penv_dir, "bin", "python")
            if util.IS_WINDOWS:
                self.python_exe = os.path.join(self.penv_dir, "Scripts", "python.exe")
            self.install_pip()
            return self.python_exe

        raise exception.PIOInstallerException(
            "Could not create PIO Core Virtual Environment. "
            "Please create it manually -> http://bit.ly/pio-core-virtualenv"
        )
