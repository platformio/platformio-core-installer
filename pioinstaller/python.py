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


def check():
    assert sys.platform != "cygwin"
    assert (
        sys.version_info >= (2, 7, 9) and sys.version_info < (3,)
    ) or sys.version_info >= (3, 5)
    if sys.platform.lower().startswith("win"):
        assert not any(s in sys.executable.lower() for s in ("msys", "mingw", "emacs"))
        assert os.path.isdir(os.path.join(sys.prefix, "Scripts")) or (
            sys.version_info >= (3, 5) and __import__("venv")
        )
    return True