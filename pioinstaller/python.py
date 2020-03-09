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

from pioinstaller.util import get_pythonexe_path


def is_conda():
    return any(
        [
            os.path.exists(os.path.join(sys.prefix, "conda-meta")),
            # (os.getenv("CONDA_PREFIX") or os.getenv("CONDA_DEFAULT_ENV")),
            ("anaconda" in sys.executable) or ("miniconda" in sys.executable),
            ("Continuum Analytics" in sys.version) or ("conda" in sys.version),
        ]
    )


def check():
    assert sys.platform != "cygwin"

    # version check
    assert (
        sys.version_info >= (2, 7, 9) and sys.version_info < (3,)
    ) or sys.version_info >= (3, 5)

    # conda check
    assert not is_conda()

    if not sys.platform.lower().startswith("win"):
        return True

    # windows check
    assert not any(
        s in get_pythonexe_path().lower() for s in ("msys", "mingw", "emacs")
    )
    assert os.path.isdir(os.path.join(sys.prefix, "Scripts")) or (
        sys.version_info >= (3, 5) and __import__("venv")
    )
    return True
