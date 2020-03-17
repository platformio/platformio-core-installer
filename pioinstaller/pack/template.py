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

# pylint:disable=bad-option-value,import-outside-toplevel

import os
import shutil
import sys
import tempfile
from base64 import b64decode

DEPENDENCIES = b"""
{zipfile_content}
"""


def bootstrap():
    import pioinstaller.__main__

    pioinstaller.__main__.main()


def main():
    tmpdir = None
    try:
        tmpdir = tempfile.mkdtemp()

        pioinstaller_zip = os.path.join(tmpdir, "pioinstaller.zip")
        with open(pioinstaller_zip, "wb") as fp:
            fp.write(b64decode(DEPENDENCIES))

        sys.path.insert(0, pioinstaller_zip)
        
        try:
            # pylint:disable=protected-access
            import click._unicodefun

            if sys.version_info[0] == 2:
                click._unicodefun._check_for_unicode_literals()
            else:
                click._unicodefun._verify_python3_env()
        except:  # pylint:disable=bare-except
            os.environ["LANG"] = "en_US.UTF-8"
            os.environ["LC_ALL"] = "en_US.UTF-8"
        
        bootstrap()
    finally:
        if tmpdir:
            shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    main()
