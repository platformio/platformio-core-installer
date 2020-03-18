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
import sys

import click

from pioinstaller import __title__, __version__, core, exception, util
from pioinstaller.pack import packer
from pioinstaller.python import check as python_check

log = logging.getLogger(__name__)


@click.group(name="main", invoke_without_command=True)
@click.version_option(__version__, prog_name=__title__)
@click.option("--verbose", is_flag=True, default=False, help="Verbose output")
@click.option("--shutdown-piohome/--no-shutdown-piohome", is_flag=True, default=True)
@click.option("--dev", is_flag=True, default=False)
@click.option("--ignore-python", multiple=True)
@click.pass_context
def cli(
    ctx, verbose, shutdown_piohome, dev, ignore_python
):  # pylint:disable=too-many-arguments
    if verbose:
        logging.getLogger("pioinstaller").setLevel(logging.DEBUG)

    if not ctx.invoked_subcommand:
        click.echo("Installer version: %s" % __version__)
        click.echo("Platform: %s" % platform.platform())
        click.echo("Python version: %s" % sys.version)
        click.echo("Python path: %s" % sys.executable)
        try:
            core.install_platformio_core(shutdown_piohome, dev, ignore_python)
        except exception.PIOInstallerException as e:
            raise click.ClickException(str(e))


@cli.command()
@click.argument(
    "target",
    default=os.getcwd,
    required=False,
    type=click.Path(
        exists=False, file_okay=True, dir_okay=True, writable=True, resolve_path=True
    ),
)
def pack(target):
    return packer.pack(target)


@cli.group()
def check():
    pass


@check.command()
def python():
    try:
        python_check()
        click.secho(
            "The Python %s (%s) interpreter is compatible."
            % (platform.python_version(), util.get_pythonexe_path()),
            fg="green",
        )
    except exception.IncompatiblePythonError as e:
        raise click.ClickException(str(e))


def main():
    return cli()  # pylint: disable=no-value-for-parameter


if __name__ == "__main__":
    sys.exit(main())
