# Copyright 2019-present PlatformIO Labs <contact@piolabs.com>

import click

from pioinstaller import __title__, __version__


@click.group()
@click.version_option(__version__, prog_name=__title__)
def cli():
    pass


def main() -> int:
    return cli()
