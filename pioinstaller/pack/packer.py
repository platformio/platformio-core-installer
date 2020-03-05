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
import subprocess
import tempfile
import zipfile

from pioinstaller.exception import InvalidFileFormat

PACK_ROOT = os.path.abspath(os.path.dirname(__file__))
PROJECT_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(PACK_ROOT)))


def create_wheels(package_dir, dest_dir):
    subprocess.run(
        ["pip", "wheel", "--wheel-dir", dest_dir, "."], check=True, cwd=package_dir
    )


def process_target(target):
    _, ext = os.path.splitext(target)
    if not ext:
        return os.path.join(target, "get-platformio.py")
    if ext != ".py":
        raise InvalidFileFormat(".py")
    return target


def pack(target=os.path.join(PROJECT_ROOT, "get-platformio.py"),):
    assert isinstance(target, str)

    target = process_target(target)

    with tempfile.TemporaryDirectory() as tmpdir:
        create_wheels(PROJECT_ROOT, tmpdir)

        new_data = io.BytesIO()
        for whl in os.listdir(tmpdir):
            with zipfile.ZipFile(os.path.join(tmpdir, whl)) as existing_zip:
                with zipfile.ZipFile(new_data, mode="a") as new_zip:
                    for zinfo in existing_zip.infolist():
                        if re.search(r"\.dist-info/", zinfo.filename):
                            continue
                        new_zip.writestr(zinfo, existing_zip.read(zinfo))
        zipdata = base64.b85encode(new_data.getvalue()).decode("utf8")
        chunked = []
        for i in range(0, len(zipdata), 79):
            chunked.append(zipdata[i : i + 79])
        os.makedirs(os.path.dirname(target), exist_ok=True)

        with open(target, "w") as fp:
            with open(
                os.path.join(PACK_ROOT, "template.py"), "r", encoding="utf8"
            ) as fp_template:
                fp.write(
                    fp_template.read().format(
                        installed_version="latest", zipfile_content="\n".join(chunked),
                    ),
                )

        # Ensure the permissions on the newly created file
        oldmode = os.stat(target).st_mode & 0o7777
        newmode = (oldmode | 0o555) & 0o7777
        os.chmod(target, newmode)
    return target
