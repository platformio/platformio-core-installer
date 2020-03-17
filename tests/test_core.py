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

import os
import subprocess

from pioinstaller import core, penv, util


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
