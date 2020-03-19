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


class PIOInstallerException(Exception):

    MESSAGE = None

    def __str__(self):  # pragma: no cover
        if self.MESSAGE:
            # pylint: disable=not-an-iterable
            return self.MESSAGE.format(*self.args)

        return super(PIOInstallerException, self).__str__()


class IncompatiblePythonError(PIOInstallerException):

    MESSAGE = "{0}"


class DistutilsNotFound(PIOInstallerException):

    MESSAGE = "Could not find distutils module"


class InvalidPlatformIOCore(PIOInstallerException):

    MESSAGE = "{0}"
