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
    # platform check
    if sys.platform == "cygwin":
        raise exception.IncompatiblePythonError("Unsupported cygwin platform")

    # version check
    if not (
        sys.version_info >= (2, 7, 9) and sys.version_info < (3,)
    ) and not sys.version_info >= (3, 5):
        raise exception.IncompatiblePythonError(
            "Unsupported python version: %s. "
            "Supported version: >= 2.7.9 and < 3, or >= 3.5" % sys.version,
        )

    # conda check
    if is_conda():
        raise exception.IncompatiblePythonError("Conda is not supported")

    if not util.IS_WINDOWS:
        return True

    # windows check
    if any(s in util.get_pythonexe_path().lower() for s in ("msys", "mingw", "emacs")):
        raise exception.IncompatiblePythonError("Unsupported platform: ")

    if not os.path.isdir(os.path.join(sys.prefix, "Scripts")):
        raise exception.IncompatiblePythonError("Cannot find Scripts folder")

    if not (sys.version_info >= (3, 5) and __import__("venv")):
        raise exception.IncompatiblePythonError("Cannot find venv module")

    return True


def find_compatible_pythons():
    exenames = ["python3", "python", "python2"]
    if util.IS_WINDOWS:
        exenames = ["python.exe"]
    log.debug("Current environment PATH %s", os.getenv("PATH"))
    candidates = []
    for exe in exenames:
        for path in os.getenv("PATH").split(os.pathsep):
            if not os.path.isfile(os.path.join(path, exe)):
                continue
            candidates.append(os.path.join(path, exe))
    result = []
    for item in candidates:
        log.debug("Checking a Python candidate %s", item)
        try:
            subprocess.check_output(
                [
                    item,
                    util.get_installer_script(),
                    "--no-shutdown-piohome",
                    "--silent",
                    "check",
                    "python",
                ]
            )
            result.append(item)
            log.debug("Found a compatible Python %s", item)
        except:  # pylint:disable=bare-except
            pass
    return result
