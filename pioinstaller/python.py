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
import platform
import subprocess
import sys

from pioinstaller import core, exception, util

log = logging.getLogger(__name__)


PORTABLE_PYTHONS = {
    "windows_x86": "https://dl.bintray.com/platformio/dl-misc/"
    "python-portable-windows_x86-3.7.6.tar.gz",
    "windows_amd64": "https://dl.bintray.com/platformio/dl-misc/"
    "python-portable-windows_amd64-3.7.6.tar.gz",
}


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


def is_portable():
    try:
        import winpython  # pylint:disable=bad-option-value, import-outside-toplevel, unused-import, import-error, unused-variable

        return True
    except:  # pylint:disable=bare-except
        return False


def download_portable(core_dir):
    cache_dir = core.get_cache_dir(core_dir)
    log.debug("Trying download portable python")
    link = PORTABLE_PYTHONS.get(util.get_systype())
    if not link:
        return None
    try:
        log.debug("Downloading portable python...")
        archive_path = util.download_file(
            link, os.path.join(cache_dir, os.path.basename(link))
        )

        python_path = os.path.join(core_dir, "python37")
        util.safe_remove_dir(python_path)
        util.safe_create_dir(python_path, raise_exception=True)

        log.debug("Unpacking portable python...")
        util.unpack_archive(archive_path, python_path)
        if util.IS_WINDOWS:
            return os.path.join(python_path, "python.exe")
        return os.path.join(python_path, "python")
    except:  # pylint:disable=bare-except
        log.debug("Could not download portable python")


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
            "Supported version: >= 2.7.9 and < 3, or >= 3.5"
            % platform.python_version(),
        )

    # conda check
    if is_conda():
        raise exception.IncompatiblePythonError("Conda is not supported")

    if not util.IS_WINDOWS:
        return True

    # windows check
    if any(s in util.get_pythonexe_path().lower() for s in ("msys", "mingw", "emacs")):
        raise exception.IncompatiblePythonError("Unsupported platform: ")

    try:
        assert os.path.isdir(os.path.join(sys.prefix, "Scripts")) or (
            sys.version_info >= (3, 5) and __import__("venv")
        )
    except (AssertionError, ImportError):
        raise exception.IncompatiblePythonError(
            "Unsupported python without 'Scripts' folder and 'venv' module"
        )

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
    if sys.executable not in candidates:
        if sys.version_info >= (3,):
            candidates.insert(0, sys.executable)
        else:
            candidates.append(sys.executable)
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
