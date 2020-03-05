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

import os.path
import shutil
import struct
import sys
import tempfile

# Useful for very coarse version differentiation.
PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3

if PY3:
    iterbytes = iter
else:

    def iterbytes(buf):
        return (ord(byte) for byte in buf)


try:
    from base64 import b85decode
except ImportError:
    _b85alphabet = (
        b"0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        b"abcdefghijklmnopqrstuvwxyz!#$%&()*+-;<=>?@^_`{{|}}~"
    )

    def b85decode(b):
        _b85dec = [None] * 256
        for i, c in enumerate(iterbytes(_b85alphabet)):
            _b85dec[c] = i

        padding = (-len(b)) % 5
        b = b + b"~" * padding
        out = []
        packI = struct.Struct("!I").pack
        for i in range(0, len(b), 5):
            chunk = b[i : i + 5]
            acc = 0
            try:
                for c in iterbytes(chunk):
                    acc = acc * 85 + _b85dec[c]
            except TypeError:
                for j, c in enumerate(iterbytes(chunk)):
                    if _b85dec[c] is None:
                        raise ValueError(
                            "bad base85 character at position %d" % (i + j)
                        )
                raise
            try:
                out.append(packI(acc))
            except struct.error:
                raise ValueError("base85 overflow in hunk starting at byte %d" % i)

        result = b"".join(out)
        if padding:
            result = result[:-padding]
        return result


def bootstrap():
    import pioinstaller.__main__  # pylint:disable=import-outside-toplevel

    pioinstaller.__main__.main()


def main():
    tmpdir = None
    try:
        tmpdir = tempfile.mkdtemp()

        pioinstaller_zip = os.path.join(tmpdir, "pioinstaller.zip")
        with open(pioinstaller_zip, "wb") as fp:
            fp.write(b85decode(DATA.replace(b"\n", b"")))

        sys.path.insert(0, pioinstaller_zip)

        bootstrap()
    finally:
        if tmpdir:
            shutil.rmtree(tmpdir, ignore_errors=True)


DATA = b"""
{zipfile_content}
"""


if __name__ == "__main__":
    main()
