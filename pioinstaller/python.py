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

import glob
import logging
import os
import platform
import subprocess
import sys
import tempfile

import click

from pioinstaller import exception, util

log = logging.getLogger(__name__)


PORTABLE_PYTHONS = {
    "windows_x86": (
        "https://dl.bintray.com/platformio/dl-misc/"
        "python-portable-windows_x86-3.7.7.tar.gz"
    ),
    "windows_amd64": (
        "https://dl.bintray.com/platformio/dl-misc/"
        "python-portable-windows_amd64-3.7.7.tar.gz"
    ),
    "darwin_x86_64": (
        "https://dl.bintray.com/platformio/dl-misc/"
        "python-portable-darwin_x86_64-3.8.4.tar.gz"
    ),
}


def is_conda():
    return any(
        [
            os.path.exists(os.path.join(sys.prefix, "conda-meta")),
            # (os.getenv("CONDA_PREFIX") or os.getenv("CONDA_DEFAULT_ENV")),
            "anaconda" in sys.executable.lower(),
            "miniconda" in sys.executable.lower(),
            "continuum analytics" in sys.version.lower(),
            "conda" in sys.version.lower(),
        ]
    )


def is_portable():
    try:
        __import__("winpython")

        return True
    except:  # pylint:disable=bare-except
        return False


def fetch_portable_python(dst):
    url = PORTABLE_PYTHONS.get(util.get_systype())
    if not url:
        log.debug("There is no portable Python for %s", util.get_systype())
        return None
    try:
        log.debug("Downloading portable python...")

        archive_path = util.download_file(
            url, os.path.join(os.path.join(dst, ".cache", "tmp"), os.path.basename(url))
        )

        python_dir = os.path.join(dst, "python3")
        util.safe_remove_dir(python_dir)
        util.safe_create_dir(python_dir, raise_exception=True)

        log.debug("Unpacking portable python...")
        util.unpack_archive(archive_path, python_dir)
        if util.IS_WINDOWS:
            return os.path.join(python_dir, "python.exe")
        return os.path.join(python_dir, "bin", "python3")
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

    try:
        __import__("distutils.command")
    except ImportError:
        raise exception.DistutilsNotFound()

    # portable Python 3 for macOS is not compatible with macOS < 10.13
    # https://github.com/platformio/platformio-core-installer/issues/70
    if util.IS_MACOS and sys.version_info >= (3, 5):
        with tempfile.NamedTemporaryFile() as tmpfile:
            os.utime(tmpfile.name)

    if not util.IS_WINDOWS:
        return True

    # windows check
    if any(s in util.get_pythonexe_path().lower() for s in ("msys", "mingw", "emacs")):
        raise exception.IncompatiblePythonError(
            "Unsupported environments: msys, mingw, emacs >> %s"
            % util.get_pythonexe_path(),
        )

    try:
        assert os.path.isdir(os.path.join(sys.prefix, "Scripts")) or (
            sys.version_info >= (3, 5) and __import__("venv")
        )
    except (AssertionError, ImportError):
        raise exception.IncompatiblePythonError(
            "Unsupported python without 'Scripts' folder and 'venv' module"
        )

    return True


def find_compatible_pythons(ignore_pythons=None):  # pylint: disable=too-many-branches
    ignore_list = []
    for p in ignore_pythons or []:
        ignore_list.extend(glob.glob(p))
    exenames = ["python3", "python", "python2"]
    if util.IS_WINDOWS:
        exenames = ["%s.exe" % item for item in exenames]
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
        if item in ignore_list:
            continue
        log.debug("Checking a Python candidate %s", item)
        try:
            output = subprocess.check_output(
                [
                    item,
                    util.get_installer_script(),
                    "--no-shutdown-piohome",
                    "check",
                    "python",
                ],
                stderr=subprocess.STDOUT,
            )
            result.append(item)
            try:
                log.debug(output.decode().strip())
            except UnicodeDecodeError:
                pass
        except subprocess.CalledProcessError as e:  # pylint:disable=bare-except
            try:
                error = e.output.decode()
                log.debug(error)
            except UnicodeDecodeError:
                pass
            error = error or ""
            if "Could not find distutils module" in error:
                # pylint:disable=line-too-long
                raise click.ClickException(
                    """Can not install PlatformIO Core due to a missed `distutils` package in your Python installation.
Please install this package manually using the OS package manager. For example:

$ apt-get install python3-venv

(MAY require administrator access `sudo`)""",
                )
    return result
