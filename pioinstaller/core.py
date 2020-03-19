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
import logging
import os
import platform
import subprocess
import sys
import time

import click
import semantic_version

from pioinstaller import exception, home, util

log = logging.getLogger(__name__)

PIO_CORE_DEVELOP_URL = "https://github.com/platformio/platformio/archive/develop.zip"
UPDATE_INTERVAL = 60 * 60 * 24 * 3  # 3 days


def get_core_dir():
    if os.getenv("PLATFORMIO_CORE_DIR"):
        return os.getenv("PLATFORMIO_CORE_DIR")

    core_dir = os.path.join(util.expanduser("~"), ".platformio")
    if not util.IS_WINDOWS or not util.has_non_ascii_char(core_dir):
        return core_dir

    win_core_dir = os.path.splitdrive(core_dir)[0] + "\\.platformio"
    if not os.path.isdir(win_core_dir):
        try:
            os.makedirs(win_core_dir)
            with open(os.path.join(win_core_dir, "file.tmp"), "w") as fp:
                fp.write("test")
            os.remove(os.path.join(win_core_dir, "file.tmp"))
            return win_core_dir
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
    try:
        home.install_pio_home(platformio_exe)
    except Exception as e:  # pylint:disable=broad-except
        log.debug(e)

    click.secho(
        "\nPlatformIO Core has been successfully installed into an isolated environment `%s`!\n"
        % penv_dir,
        fg="green",
    )
    click.secho(
        "The `platformio.exe` is located at: `%s`\n" % platformio_exe, fg="cyan"
    )
    # pylint:disable=line-too-long
    click.secho(
        """If you need access to `platformio.exe` from other applications, please install shell commands
(add PlatformIO Core binary directory `%s` to system environment PATH variable):
https://docs.platformio.org/en/page/installation.html#install-shell-commands
"""
        % penv.get_penv_bin_dir(penv_dir),
        fg="cyan",
    )
    return True


def check(dev=False, auto_upgrade=False, version_requirements=None):

    # pylint: disable=bad-option-value, import-outside-toplevel, unused-import, import-error, unused-variable, cyclic-import
    from pioinstaller import penv

    platformio_exe = os.path.join(
        penv.get_penv_bin_dir(), "platformio.exe" if util.IS_WINDOWS else "platformio",
    )
    if not os.path.isfile(platformio_exe):
        raise exception.InvalidPlatformIOCore(
            "PlatformIO executable not found in `%s`" % penv.get_penv_bin_dir()
        )

    if not os.path.isfile(os.path.join(penv.get_penv_dir(), "state.json")):
        raise exception.InvalidPlatformIOCore(
            "Could not found state.json file in `%s`"
            % os.path.join(penv.get_penv_dir(), "state.json")
        )

    try:
        # pylint: disable=bad-option-value, import-outside-toplevel, unused-import, import-error, unused-variable, cyclic-import
        import platformio
    except ImportError:
        raise exception.InvalidPlatformIOCore("Could not import PlatformIO module")

    pio_version = get_pio_version(platformio)
    if version_requirements:
        try:
            if pio_version in semantic_version.Spec(version_requirements):
                raise exception.InvalidPlatformIOCore(
                    "PlatformIO Core version %s does not match version requirements %s."
                    % (str(pio_version), version_requirements)
                )
        except ValueError:
            click.secho(
                "Invalid version requirements format: %s. "
                "More about Semantic Versioning: https://semver.org/"
                % version_requirements
            )

    state = None

    with open(os.path.join(penv.get_penv_dir(), "state.json")) as fp:
        state = json.load(fp)
        if state.get("platform") != platform.platform():
            raise exception.InvalidPlatformIOCore(
                "PlatformIO installed using another platform `%s`. Your platform: %s"
                % (state.get("platform"), platform.platform())
            )

    try:
        subprocess.check_output([platformio_exe, "--version"], stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        error = e.output.decode()
        raise exception.InvalidPlatformIOCore(
            "Could not run `%s --version`.\nError: %s" % (platformio, str(error))
        )

    result = {"platformio_exe": platformio_exe, "version": str(pio_version)}

    if not auto_upgrade:
        return result

    time_now = int(round(time.time()))

    last_piocore_version_check = state.get("last_piocore_version_check")

    if (
        last_piocore_version_check
        and (time_now - int(last_piocore_version_check)) < UPDATE_INTERVAL
    ):
        return result

    with open(os.path.join(penv.get_penv_dir(), "state.json"), "w") as fp:
        state["last_piocore_version_check"] = time_now
        json.dump(state, fp)

    if not last_piocore_version_check:
        return result

    dev = dev or pio_version.prerelease
    upgrade_core(platformio_exe, dev)

    result["pio_version"] = get_pio_version(platformio)
    return result


def get_pio_version(platformio):
    try:
        if sys.version_info[0] == 3:
            # pylint: disable=bad-option-value, import-outside-toplevel, unused-import, import-error, unused-variable, cyclic-import
            import importlib

            importlib.reload(platformio)  # pylint:disable=no-member
        else:
            reload(platformio)
        return semantic_version.Version(util.pepver_to_semver(platformio.__version__))
    except:  # pylint:disable=bare-except
        return platformio.__version__


def upgrade_core(platformio_exe, dev=False):
    command = [platformio_exe, "upgrade"]
    if dev:
        command.append("--dev")
    try:
        subprocess.check_output(
            command, stderr=subprocess.PIPE,
        )
        return True
    except Exception as e:  # pylint:disable=broad-except
        raise exception.PIOInstallerException(
            "Could not upgrade PlatformIO Core: %s" % str(e)
        )
