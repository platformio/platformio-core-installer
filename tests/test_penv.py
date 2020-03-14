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
import os
import subprocess

from pioinstaller import __version__, penv, python, util


def test_penv_with_default_python(pio_installer_script, tmpdir, monkeypatch):
    monkeypatch.setattr(util, "get_installer_script", lambda: pio_installer_script)

    penv_path = str(tmpdir.mkdir("penv"))
    assert penv.create_virtualenv(penv_path)

    python_exe = os.path.join(penv_path, "bin", "python")
    if util.IS_WINDOWS:
        python_exe = os.path.join(penv_path, "Scripts", "python.exe")
    assert (
        subprocess.check_call([python_exe, pio_installer_script, "check", "python"])
        == 0
    )
    with open(os.path.join(penv_path, "state.json")) as fp:
        json_info = json.load(fp)
        assert json_info.get("installer_version") == __version__


def test_penv_with_downloadable_venv(pio_installer_script, tmpdir, monkeypatch):
    monkeypatch.setattr(util, "get_installer_script", lambda: pio_installer_script)

    penv_path = str(tmpdir.mkdir("penv"))

    python_exes = python.find_compatible_pythons()
    if not python_exes:
        raise Exception("Python executable not found.")
    python_exe = python_exes[0]

    assert penv.create_virtualenv_with_external_script(python_exe, penv_path)

    python_exe = os.path.join(penv_path, "bin", "python")
    if util.IS_WINDOWS:
        python_exe = os.path.join(penv_path, "Scripts", "python.exe")
    assert (
        subprocess.check_call([python_exe, pio_installer_script, "check", "python"])
        == 0
    )


def test_penv_with_portable_python(pio_installer_script, tmpdir, monkeypatch):
    if not util.IS_WINDOWS:
        return
    monkeypatch.setattr(util, "get_installer_script", lambda: pio_installer_script)

    penv_path = str(tmpdir.mkdir("penv"))
    python_exe = penv.download_portable_python()
    assert penv.create_virtualenv_with_python_executable(python_exe, penv_path)

    python_exe = os.path.join(penv_path, "bin", "python")
    if util.IS_WINDOWS:
        python_exe = os.path.join(penv_path, "Scripts", "python.exe")
    assert (
        subprocess.check_call([python_exe, pio_installer_script, "check", "python"])
        == 0
    )
