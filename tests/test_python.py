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
import sys

import pytest

from pioinstaller import util


def test_check_default_python(pio_installer_script):
    python_exe = os.path.join(
        sys.real_prefix if hasattr(sys, "real_prefix") else sys.prefix,
        "Scripts" if util.IS_WINDOWS else "bin",
        "python%s.exe" % sys.version_info[0]
        if util.IS_WINDOWS
        else "python%s" % sys.version_info[0],
    )
    assert (
        subprocess.check_call([python_exe, pio_installer_script, "check", "python"])
        == 0
    )


def test_check_conda_python(pio_installer_script):
    if not os.getenv("MINICONDA"):
        return
    with pytest.raises(subprocess.CalledProcessError) as excinfo:
        subprocess.check_call(
            [os.getenv("MINICONDA"), pio_installer_script, "check", "python"]
        )
