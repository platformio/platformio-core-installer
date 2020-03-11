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

import os
import sys

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
