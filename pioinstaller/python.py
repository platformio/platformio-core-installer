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
import json
import logging
import os
import platform
import subprocess
import sys
import tempfile

import click
import requests
import semantic_version

from pioinstaller import exception, util

log = logging.getLogger(__name__)


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
        pass
    print(os.path.normpath(sys.executable))
    python_dir = os.path.dirname(sys.executable)
    if not util.IS_WINDOWS:
        # skip "bin" folder
        python_dir = os.path.dirname(python_dir)
    manifest_path = os.path.join(python_dir, "package.json")
    if not os.path.isfile(manifest_path):
        return False
    try:
        with open(manifest_path) as fp:
            return json.load(fp).get("name") == "python-portable"
    except ValueError:
        pass
    return False


def fetch_portable_python(dst):
    url = get_portable_python_url()
    if not url:
        log.debug("Could not find portable Python for %s", util.get_systype())
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
    return None


def get_portable_python_url():
    systype = util.get_systype()
    result = requests.get(
        "https://api.registry.platformio.org/v3/packages/"
        "platformio/tool/python-portable",
        timeout=10,
    ).json()
    versions = [
        version
        for version in result["versions"]
        if is_version_system_compatible(version, systype)
    ]
    best_version = {}
    for version in versions:
        if not best_version or semantic_version.Version(
            version["name"]
        ) > semantic_version.Version(best_version["name"]):
            best_version = version
    for item in best_version.get("files", []):
        if systype in item["system"]:
            return item["download_url"]
    return None


def is_version_system_compatible(version, systype):
    return any(systype in item["system"] for item in version["files"])


def check():
    # platform check
    if sys.platform == "cygwin":
        raise exception.IncompatiblePythonError("Unsupported Cygwin platform")

    # version check
    if sys.version_info < (3, 6):
        raise exception.IncompatiblePythonError(
            "Unsupported Python version: %s. "
            "Minimum supported Python version is 3.6 or above."
            % platform.python_version(),
        )

    # conda check
    if is_conda():
        raise exception.IncompatiblePythonError("Conda is not supported")

    try:
        __import__("ensurepip")
        __import__("venv")
        # __import__("distutils.command")
    except ImportError:
        raise exception.PythonVenvModuleNotFound()

    # portable Python 3 for macOS is not compatible with macOS < 10.13
    # https://github.com/platformio/platformio-core-installer/issues/70
    if util.IS_MACOS:
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


def find_compatible_pythons(
    ignore_pythons=None, raise_exception=True
):  # pylint: disable=too-many-branches
    ignore_list = []
    for p in ignore_pythons or []:
        ignore_list.extend(glob.glob(p))
    exenames = [
        "python3",  # system Python
        "python3.11",
        "python3.10",
        "python3.9",
        "python3.8",
        "python3.7",
        "python",
    ]
    if util.IS_WINDOWS:
        exenames = ["%s.exe" % item for item in exenames]
    log.debug("Current environment PATH %s", os.getenv("PATH"))
    candidates = []
    for exe in exenames:
        for path in os.getenv("PATH").split(os.pathsep):
            if not os.path.isfile(os.path.join(path, exe)):
                continue
            candidates.append(os.path.join(path, exe))

    if sys.executable in candidates:
        candidates.remove(sys.executable)
    # put current Python to the top of list
    candidates.insert(0, sys.executable)

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
        except subprocess.CalledProcessError as e:
            error = None
            try:
                error = e.output.decode()
                log.debug(error)
            except UnicodeDecodeError:
                pass
            if error and "`venv` module" in error:
                # pylint:disable=line-too-long
                raise click.ClickException(
                    """Can not install PlatformIO Core due to a missed `venv` module in your Python installation.
Please install this package manually using the OS package manager. For example:

$ apt-get install python3-venv

(MAY require administrator access `sudo`)""",
                )
        except Exception as e:  # pylint: disable=broad-except
            log.debug(e)

    if not result and raise_exception:
        raise exception.IncompatiblePythonError(
            "Could not find compatible Python 3.6 or above in your system."
            "Please install the latest official Python 3 and restart installation:\n"
            "https://docs.platformio.org/page/faq.html#install-python-interpreter"
        )

    return result
