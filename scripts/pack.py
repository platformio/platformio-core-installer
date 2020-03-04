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
import pathlib
import re
import subprocess
import tempfile
import zipfile

PROJECT_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


def _path(pyversion=None):
    parts = [PROJECT_ROOT, pyversion, "get-platformio.py"]
    return os.path.join(*filter(None, parts))


def _template(name="default.py"):
    return os.path.join(PROJECT_ROOT, "templates", name)


def create_wheels(package_dir: str, dest_dir: str):
    subprocess.run(
        ["pip", "wheel", "--wheel-dir", dest_dir, "."], check=True, cwd=package_dir
    )


def main(installer_path=_path(), template_path=_template()):
    with tempfile.TemporaryDirectory() as tmpdir:
        create_wheels("/Users/rs/WORK/platformio-core-installer", tmpdir)

        new_data = io.BytesIO()
        for whl in pathlib.Path(tmpdir).iterdir():
            with zipfile.ZipFile(whl) as existing_zip:
                with zipfile.ZipFile(new_data, mode="a") as new_zip:
                    for zinfo in existing_zip.infolist():
                        if re.search(r"\.dist-info/", zinfo.filename):
                            continue
                        new_zip.writestr(zinfo, existing_zip.read(zinfo))
        zipdata = base64.b85encode(new_data.getvalue()).decode("utf8")
        chunked = []
        for i in range(0, len(zipdata), 79):
            chunked.append(zipdata[i : i + 79])
        os.makedirs(os.path.dirname(installer_path), exist_ok=True)

        # Load our wrapper template
        with open(template_path, "r", encoding="utf8") as fp:
            WRAPPER_TEMPLATE = fp.read()

        with open(installer_path, "w") as fp:
            fp.write(
                WRAPPER_TEMPLATE.format(
                    installed_version="latest", zipfile="\n".join(chunked),
                ),
            )

        # Ensure the permissions on the newly created file
        oldmode = os.stat(installer_path).st_mode & 0o7777
        newmode = (oldmode | 0o555) & 0o7777
        os.chmod(installer_path, newmode)


if __name__ == "__main__":
    main()
