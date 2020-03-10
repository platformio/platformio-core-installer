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

from pioinstaller import exception, util

log = logging.getLogger(__name__)


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
    log.debug("sys.platform: %s", sys.platform)
    log.debug("sys.version: %s", sys.version)
    log.debug("sys.executable: %s", sys.executable)

    # platform check
    if sys.platform == "cygwin":
        raise exception.IncompatiblePythonError("Unsupported cygwin platform.")

    # version check
    if not (
        sys.version_info >= (2, 7, 9) and sys.version_info < (3,)
    ) and not sys.version_info >= (3, 5):
        raise exception.IncompatiblePythonError(
            "Unsupported python version. "
            "Supported version: >= 2.7.9 and < 3, or >= 3.5."
        )

    # conda check
    if is_conda():
        raise exception.IncompatiblePythonError("Conda not supported.")

    if not util.IS_WINDOWS:
        return True

    # windows check
    if any(s in util.get_pythonexe_path().lower() for s in ("msys", "mingw", "emacs")):
        raise exception.IncompatiblePythonError(
            "Unsupported msys, mingw, emacs platforms."
        )

    if not os.path.isdir(os.path.join(sys.prefix, "Scripts")):
        raise exception.IncompatiblePythonError("Cannot find Scripts folder.")

    if not (sys.version_info >= (3, 5) and __import__("venv")):
        raise exception.IncompatiblePythonError("Cannot find venv module.")

    return True


def find_compatible_pythons():
    exenames = ["python3", "python", "python2"]
    if util.IS_WINDOWS:
        exenames = ["python.exe"]
    result = []
    log.debug("Current environment PATH %s", os.getenv("PATH"))
    for path in os.getenv("PATH").split(os.pathsep):
        for exe in exenames:
            if not os.path.isfile(os.path.join(path, exe)):
                continue
            log.debug("Found a Python candidate %s", path)
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
            result.append(os.path.join(path, exe))
    return result
