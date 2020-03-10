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

from pioinstaller import util


def is_conda():
    return any(
        [
            os.path.exists(os.path.join(sys.prefix, "conda-meta")),
            # (os.getenv("CONDA_PREFIX") or os.getenv("CONDA_DEFAULT_ENV")),
            "anaconda" in sys.executable,
            "miniconda" in sys.executable,
            "Continuum Analytics" in sys.version,
            "conda" in sys.version,
        ]
    )


def check():
    assert sys.platform != "cygwin"

    # version check
    assert (
        sys.version_info >= (2, 7, 9) and sys.version_info < (3,)
    ) or sys.version_info >= (3, 5)

    # conda check
    assert not is_conda()

    if not util.IS_WINDOWS:
        return True

    # windows check
    assert not any(
        s in util.get_pythonexe_path().lower() for s in ("msys", "mingw", "emacs")
    )
    assert os.path.isdir(os.path.join(sys.prefix, "Scripts")) or (
        sys.version_info >= (3, 5) and __import__("venv")
    )
    return True


def find_compatible_pythons():
    exenames = ["python3", "python", "python2"]
    if util.IS_WINDOWS:
        exenames = ["python.exe"]
    compatible_exes = []
    for path in os.getenv("PATH").split(os.pathsep):
        for exe in exenames:
            if not os.path.isfile(os.path.join(path, exe)):
                continue
            if (
                subprocess.call(
                    [
                        os.path.join(path, exe),
                        os.path.abspath(sys.argv[0]),
                        "check",
                        "python",
                    ]
                )
                != 0
            ):
                continue
            compatible_exes.append(os.path.join(path, exe))
    return compatible_exes
