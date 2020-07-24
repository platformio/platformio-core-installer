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

import base64
import io
import os
import re
import shutil
import subprocess
import tempfile
import zipfile

from pioinstaller import util


def create_wheels(package_dir, dest_dir):
    subprocess.call(["pip", "wheel", "--wheel-dir", dest_dir, "."], cwd=package_dir)


def pack(target):
    assert isinstance(target, str)

    if os.path.isdir(target):
        target = os.path.join(target, "get-platformio.py")
    if not os.path.isdir(os.path.dirname(target)):
        os.makedirs(os.path.dirname(target))

    tmp_dir = tempfile.mkdtemp()
    create_wheels(os.path.dirname(util.get_source_dir()), tmp_dir)

    new_data = io.BytesIO()
    for whl in os.listdir(tmp_dir):
        with zipfile.ZipFile(os.path.join(tmp_dir, whl)) as existing_zip:
            with zipfile.ZipFile(new_data, mode="a") as new_zip:
                for zinfo in existing_zip.infolist():
                    if re.search(r"\.dist-info/", zinfo.filename):
                        continue
                    new_zip.writestr(zinfo, existing_zip.read(zinfo))
    zipdata = base64.b64encode(new_data.getvalue()).decode("utf8")
    with open(target, "w") as fp:
        with open(os.path.join(util.get_source_dir(), "pack", "template.py")) as fptlp:
            fp.write(fptlp.read().format(zipfile_content=zipdata))

    # Ensure the permissions on the newly created file
    oldmode = os.stat(target).st_mode & 0o7777
    newmode = (oldmode | 0o555) & 0o7777
    os.chmod(target, newmode)

    # Clearing up
    shutil.rmtree(tmp_dir)

    return target
