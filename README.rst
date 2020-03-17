PlatformIO Core Installer
=========================

.. image:: https://travis-ci.org/platformio/platformio-core-installer.svg?branch=develop
    :target: https://travis-ci.org/platformio/platformio-core-installer
    :alt: Travis.CI Build Status
.. image:: https://ci.appveyor.com/api/projects/status/2crg7e2oxutmk07r/branch/develop?svg=true
    :target: https://ci.appveyor.com/project/ivankravets/platformio-core-installer
    :alt: AppVeyor.CI Build Status
.. image:: https://img.shields.io/badge/license-Apache%202.0-blue.svg
    :target: https://pypi.python.org/pypi/platformio/
    :alt:  License

Standalone installer for PlatformIO Core.

Using on Unix (FreeBSD, Linux, macOS, etc.)
-------------------------------------------

Run this command:

.. code-block::
 
   python -c "$(curl -fsSL https://raw.githubusercontent.com/platformio/platformio-core-installer/develop/get-platformio.py)"

Using on Windows
----------------

1. Install the latest Python 3 following `this guide <https://docs.platformio.org/en/latest/faq.html#install-python-interpreter>`_
2. Download https://raw.githubusercontent.com/platformio/platformio-core-installer/develop/get-platformio.py
3. Run this command

.. code-block::

    python get-platformio.py

