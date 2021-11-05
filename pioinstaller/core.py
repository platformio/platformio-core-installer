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

# pylint: disable=import-outside-toplevel

import json
import logging
import os
import platform
import subprocess
import sys
import time

import click
import semantic_version

from pioinstaller import __version__, exception, home, util

log = logging.getLogger(__name__)

PIO_CORE_DEVELOP_URL = "https://github.com/platformio/platformio/archive/develop.zip"
UPDATE_INTERVAL = 60 * 60 * 24 * 3  # 3 days


def get_core_dir(force_to_root=False):
    if os.getenv("PLATFORMIO_CORE_DIR"):
        return os.getenv("PLATFORMIO_CORE_DIR")

    core_dir = os.path.join(util.expanduser("~"), ".platformio")
    if not util.IS_WINDOWS:
        return core_dir

    win_root_dir = os.path.splitdrive(core_dir)[0] + "\\.platformio"
    if os.path.isdir(win_root_dir):
        return win_root_dir
    try:
        if util.has_non_ascii_char(core_dir) or force_to_root:
            os.makedirs(win_root_dir)
            with open(os.path.join(win_root_dir, "file.tmp"), "w") as fp:
                fp.write("test")
            os.remove(os.path.join(win_root_dir, "file.tmp"))
            return win_root_dir
    except:  # pylint:disable=bare-except
        pass

    return core_dir


def get_cache_dir(path=None):
    core_dir = path or get_core_dir()
    path = os.path.join(core_dir, ".cache")
    if not os.path.isdir(path):
        os.makedirs(path)
    return path


def install_platformio_core(shutdown_piohome=True, develop=False, ignore_pythons=None):
    try:
        return _install_platformio_core(
            shutdown_piohome=shutdown_piohome,
            develop=develop,
            ignore_pythons=ignore_pythons,
        )
    except subprocess.CalledProcessError as exc:
        # Issue #221: Workaround for Windows OS when username contains a space
        # https://github.com/platformio/platformio-core-installer/issues/221
        if (
            util.IS_WINDOWS
            and " " in get_core_dir()
            and " " not in get_core_dir(force_to_root=True)
        ):
            return _install_platformio_core(
                shutdown_piohome=shutdown_piohome,
                develop=develop,
                ignore_pythons=ignore_pythons,
            )
        raise exc


def _install_platformio_core(shutdown_piohome=True, develop=False, ignore_pythons=None):
    # pylint: disable=bad-option-value, import-outside-toplevel, unused-import, import-error, unused-variable, cyclic-import
    from pioinstaller import penv

    if shutdown_piohome:
        home.shutdown_pio_home_servers()

    penv_dir = penv.create_core_penv(ignore_pythons=ignore_pythons)
    python_exe = os.path.join(
        penv.get_penv_bin_dir(penv_dir), "python.exe" if util.IS_WINDOWS else "python"
    )
    command = [python_exe, "-m", "pip", "install", "-U"]
    if develop:
        click.echo("Installing a development version of PlatformIO Core")
        command.append(PIO_CORE_DEVELOP_URL)
    else:
        click.echo("Installing PlatformIO Core")
        command.append("platformio")
    try:
        subprocess.check_call(command)
    except Exception as e:  # pylint:disable=broad-except
        error = str(e)
        if util.IS_WINDOWS:
            error = (
                "If you have antivirus/firewall/defender software in a system,"
                " try to disable it for a while.\n %s" % error
            )
        raise exception.PIOInstallerException(
            "Could not install PlatformIO Core: %s" % error
        )
    platformio_exe = os.path.join(
        penv.get_penv_bin_dir(penv_dir),
        "platformio.exe" if util.IS_WINDOWS else "platformio",
    )

    click.secho(
        "\nPlatformIO Core has been successfully installed into an isolated environment `%s`!\n"
        % penv_dir,
        fg="green",
    )
    click.secho("The full path to `platformio.exe` is `%s`" % platformio_exe, fg="cyan")
    # pylint:disable=line-too-long
    click.secho(
        """
If you need an access to `platformio.exe` from other applications, please install Shell Commands
(add PlatformIO Core binary directory `%s` to the system environment PATH variable):

See https://docs.platformio.org/page/installation.html#install-shell-commands
"""
        % penv.get_penv_bin_dir(penv_dir),
        fg="cyan",
    )
    return True


def check(develop=False, global_=False, auto_upgrade=False, version_spec=None):
    from pioinstaller import penv

    python_exe = (
        os.path.normpath(sys.executable)
        if global_
        else os.path.join(
            penv.get_penv_bin_dir(), "python.exe" if util.IS_WINDOWS else "python"
        )
    )
    platformio_exe = (
        util.where_is_program("platformio")
        if global_
        else os.path.join(
            penv.get_penv_bin_dir(),
            "platformio.exe" if util.IS_WINDOWS else "platformio",
        )
    )
    if not os.path.isfile(platformio_exe):
        raise exception.InvalidPlatformIOCore(
            "PlatformIO executable not found in `%s`" % penv.get_penv_bin_dir()
        )
    try:
        subprocess.check_output([platformio_exe, "--version"], stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        error = e.output.decode()
        raise exception.InvalidPlatformIOCore(
            "Could not run `%s --version`.\nError: %s" % (platformio_exe, str(error))
        )

    result = {}
    try:
        result = fetch_python_state(python_exe)
    except subprocess.CalledProcessError as e:
        error = e.output.decode()
        raise exception.InvalidPlatformIOCore(
            "Could not import PlatformIO module. Error: %s" % error
        )
    piocore_version = convert_version(result.get("core_version"))
    develop = develop or bool(piocore_version.prerelease if piocore_version else False)
    result.update(
        {
            "core_dir": get_core_dir(),
            "cache_dir": get_cache_dir(),
            "penv_dir": penv.get_penv_dir(),
            "penv_bin_dir": penv.get_penv_bin_dir(),
            "platformio_exe": platformio_exe,
            "installer_version": __version__,
            "python_exe": python_exe,
            "system": util.get_systype(),
            "is_develop_core": develop,
        }
    )

    if version_spec:
        _check_core_version(piocore_version, version_spec)
    if not global_:
        _check_platform_version()
    if auto_upgrade and not global_:
        try:
            auto_upgrade_core(platformio_exe, develop)
        except:  # pylint:disable=bare-except
            pass
        # re-fetch Pyrhon state
        try:
            result.update(fetch_python_state(python_exe))
        except:  # pylint:disable=bare-except
            raise exception.InvalidPlatformIOCore("Could not import PlatformIO module")

    return result


def _check_core_version(piocore_version, version_spec):
    try:
        if piocore_version not in semantic_version.Spec(version_spec):
            raise exception.InvalidPlatformIOCore(
                "PlatformIO Core version %s does not match version requirements %s."
                % (str(piocore_version), version_spec)
            )
    except ValueError:
        click.secho(
            "Invalid version requirements format: %s. "
            "More about Semantic Versioning: https://semver.org/" % version_spec
        )


def _check_platform_version():
    from pioinstaller import penv

    state = penv.load_state()
    if state.get("platform") != platform.platform(terse=True):
        raise exception.InvalidPlatformIOCore(
            "PlatformIO Core was installed using another platform `%s`. "
            "Your current platform: %s"
            % (state.get("platform"), platform.platform(terse=True))
        )


def fetch_python_state(python_exe):
    code = """
import json
import platform
import sys

import platformio

if sys.version_info < (3, 6):
    raise Exception(
        "Unsupported Python version: %s. "
        "Minimum supported Python version is 3.6 or above."
        % platform.python_version(),
    )

state = {
   "core_version": platformio.__version__,
   "python_version": platform.python_version()
}
print(json.dumps(state))
"""
    state = subprocess.check_output(
        [
            python_exe,
            "-c",
            code,
        ],
        stderr=subprocess.STDOUT,
    )
    return json.loads(state.decode())


def convert_version(version):
    try:
        return semantic_version.Version(util.pepver_to_semver(version))
    except:  # pylint:disable=bare-except
        return None


def auto_upgrade_core(platformio_exe, develop=False):
    from pioinstaller import penv

    state = penv.load_state()
    time_now = int(round(time.time()))
    last_piocore_version_check = state.get("last_piocore_version_check")
    if (
        last_piocore_version_check
        and (time_now - int(last_piocore_version_check)) < UPDATE_INTERVAL
    ):
        return None

    state["last_piocore_version_check"] = time_now
    penv.save_state(state)
    if not last_piocore_version_check:
        return None

    command = [platformio_exe, "upgrade"]
    if develop:
        command.append("--dev")
    try:
        subprocess.check_output(
            command,
            stderr=subprocess.PIPE,
        )
        return True
    except Exception as e:  # pylint:disable=broad-except
        raise exception.PIOInstallerException(
            "Could not upgrade PlatformIO Core: %s" % str(e)
        )
    return False


def dump_state(target, state):
    assert isinstance(target, str)

    if os.path.isdir(target):
        target = os.path.join(target, "get-platformio-core-state.json")
    if not os.path.isdir(os.path.dirname(target)):
        os.makedirs(os.path.dirname(target))

    with open(target, "w") as fp:
        json.dump(state, fp)
