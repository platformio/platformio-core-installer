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


def create_temp_dir():
    try:
        cur_dir = os.path.dirname(os.path.realpath(__file__))
        tmp_dir = tempfile.mkdtemp(dir=cur_dir, prefix=".piocore-installer-")
        testscript_path = os.path.join(tmp_dir, "test.py")
        with open(testscript_path, "w") as fp:
            fp.write("print(1)")
        assert os.path.isfile(testscript_path)
        os.remove(testscript_path)
        return tmp_dir
    except (AssertionError, NameError):
        pass
    return tempfile.mkdtemp()


def bootstrap():
    import pioinstaller.__main__

    pioinstaller.__main__.main()


def main():
    runtime_tmp_dir = create_temp_dir()
    os.environ["TMPDIR"] = runtime_tmp_dir
    tmp_dir = tempfile.mkdtemp(dir=runtime_tmp_dir)
    try:
        pioinstaller_zip = os.path.join(tmp_dir, "pioinstaller.zip")
        with open(pioinstaller_zip, "wb") as fp:
            fp.write(b64decode(DEPENDENCIES))

        sys.path.insert(0, pioinstaller_zip)

        bootstrap()
    finally:
        for d in (runtime_tmp_dir, tmp_dir):
            if d and os.path.isdir(d):
                shutil.rmtree(d, ignore_errors=True)


if __name__ == "__main__":
    main()
