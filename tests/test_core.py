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

from pioinstaller import __version__, core, penv, util


def test_install_pio_core(pio_installer_script, tmpdir, monkeypatch):
    monkeypatch.setattr(util, "get_installer_script", lambda: pio_installer_script)

    core_dir = tmpdir.mkdir(".pio")
    penv_dir = str(core_dir.mkdir("penv"))
    os.environ["PLATFORMIO_CORE_DIR"] = str(core_dir)

    assert core.install_platformio_core(shutdown_piohome=False)

    python_exe = os.path.join(
        penv.get_penv_bin_dir(penv_dir), "python.exe" if util.IS_WINDOWS else "python"
    )
    assert subprocess.check_call([python_exe, "-m", "platformio", "--version"]) == 0

    core_state_path = os.path.join(str(core_dir), "core-state.json")
    try:
        subprocess.check_output(
            [
                "python",
                pio_installer_script,
                "check",
                "core",
                "--dump-state=%s" % core_state_path,
            ], stderr=subprocess.STDOUT
        )
    except subprocess.CalledProcessError as e:
        error = e.output.decode()
        print(error)
    with open(core_state_path) as fp:
        json_info = json.load(fp)
        assert json_info.get("core_dir") == str(core_dir)
        assert json_info.get("penv_dir") == penv_dir
        assert json_info.get("installer_version") == __version__
        assert json_info.get("system") == util.get_systype()

    assert os.path.isfile(
        os.path.join(
            penv.get_penv_bin_dir(penv_dir),
            "platformio.exe" if util.IS_WINDOWS else "platformio",
        )
    )
    assert os.path.isfile(
        os.path.join(str(core_dir), "packages", "contrib-piohome", "package.json")
    )
    assert os.path.isfile(
        os.path.join(str(core_dir), "packages", "contrib-pysite", "package.json")
    )
