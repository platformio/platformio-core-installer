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
import sys

import click

from pioinstaller import __title__, __version__, exception, helpers, penv, util
from pioinstaller.pack import packer
from pioinstaller.python import check as python_check

log = logging.getLogger(__name__)


@click.group(name="main", invoke_without_command=True)
@click.version_option(__version__, prog_name=__title__)
@click.option("--verbose", is_flag=True, default=False, help="Verbose output")
@click.option("--shutdown-piohome/--no-shutdown-piohome", is_flag=True, default=True)
@click.option("--silent/--no-silent", is_flag=True, default=False)
@click.pass_context
def cli(ctx, verbose, shutdown_piohome, silent):
    if verbose:
        logging.getLogger("pioinstaller").setLevel(logging.DEBUG)
    elif silent:
        logging.getLogger("pioinstaller").setLevel(logging.ERROR)
    log.info("Installer version: %s", __version__)
    log.debug("Invoke: %s", " ".join(sys.argv))
    log.debug("Platform: %s", sys.platform)
    log.info("Python version: %s", sys.version)
    log.info("Python path: %s", sys.executable)
    if shutdown_piohome:
        helpers.shutdown_pio_home_servers()
    if not ctx.invoked_subcommand:
        penv.create_virtualenv()
        log.info("Virtual environment has been successfully created!")


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
        click.echo(
            "The Python %s interpreter is compatible." % util.get_pythonexe_path()
        )
    except exception.IncompatiblePythonError as e:
        log.warning(str(e))


def main():
    return cli()  # pylint: disable=no-value-for-parameter


if __name__ == "__main__":
    sys.exit(main())
