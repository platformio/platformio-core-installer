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

import io
import os
import shutil
import stat
import sys
import tarfile

import requests

IS_WINDOWS = sys.platform.lower().startswith("win")


def get_source_dir():
    curpath = os.path.realpath(__file__)
    if not os.path.isfile(curpath):
        for p in sys.path:
            if os.path.isfile(os.path.join(p, __file__)):
                curpath = os.path.join(p, __file__)
                break
    return os.path.dirname(curpath)


def get_pythonexe_path():
    return os.environ.get("PYTHONEXEPATH", os.path.normpath(sys.executable))


def expanduser(path):
    """
    Be compatible with Python 3.8, on Windows skip HOME and check for USERPROFILE
    """
    if not IS_WINDOWS or not path.startswith("~") or "USERPROFILE" not in os.environ:
        return os.path.expanduser(path)
    return os.environ["USERPROFILE"] + path[1:]


def has_non_ascii_char(text):
    for c in text:
        if ord(c) >= 128:
            return True
    return False


def rmtree(path):
    def _onerror(func, path, __):
        st_mode = os.stat(path).st_mode
        if st_mode & stat.S_IREAD:
            os.chmod(path, st_mode | stat.S_IWRITE)
        func(path)

    return shutil.rmtree(path, onerror=_onerror)


def find_file(name, path):
    for root, _, files in os.walk(path):
        if name in files:
            return os.path.join(root, name)
    return None


def create_dir(path):
    try:
        os.makedirs(path)
        return path
    except:  # pylint:disable=bare-except
        pass


def download_file(url, dst):
    resp = requests.get(url, stream=True)
    itercontent = resp.iter_content(chunk_size=io.DEFAULT_BUFFER_SIZE)
    with open(dst, "wb") as fp:
        for chunk in itercontent:
            fp.write(chunk)
    return dst


def unpack_archive(src, dst, mode="r:gz"):
    with tarfile.open(src, mode) as fp:
        fp.extractall(dst)
    return dst
