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
import logging
import os
import platform
import re
import shutil
import stat
import sys
import tarfile

import requests

IS_WINDOWS = sys.platform.lower().startswith("win")
IS_MACOS = sys.platform.lower() == "darwin"

log = logging.getLogger(__name__)


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


def safe_create_dir(path, raise_exception=False):
    try:
        os.makedirs(path)
        return path
    except Exception as e:  # pylint: disable=broad-except
        if raise_exception:
            raise e


def download_file(url, dst, cache=True):
    if cache:
        content_length = requests.head(url).headers.get("Content-Length")
        if os.path.isfile(dst) and content_length == os.path.getsize(dst):
            log.debug("Getting from cache: %s", dst)
            return dst

    resp = requests.get(url, stream=True)
    itercontent = resp.iter_content(chunk_size=io.DEFAULT_BUFFER_SIZE)
    safe_create_dir(os.path.dirname(dst))
    with open(dst, "wb") as fp:
        for chunk in itercontent:
            fp.write(chunk)
    return dst


def unpack_archive(src, dst):
    assert src.endswith("tar.gz")
    with tarfile.open(src, mode="r:gz") as fp:
        fp.extractall(dst)
    return dst


def get_installer_script():
    return os.path.abspath(sys.argv[0])


def get_systype():
    type_ = platform.system().lower()
    arch = platform.machine().lower()
    if type_ == "windows":
        arch = "amd64" if platform.architecture()[0] == "64bit" else "x86"
    return "%s_%s" % (type_, arch) if arch else type_


def safe_remove_dir(path, raise_exception=False):
    try:
        return rmtree(path)
    except Exception as e:  # pylint: disable=broad-except
        if raise_exception:
            raise e


def pepver_to_semver(pepver):
    return re.sub(r"(\.\d+)\.?(dev|a|b|rc|post)", r"\1-\2.", pepver, 1)
