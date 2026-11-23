"""Punto de entrada del ejecutable (PyInstaller)."""

import sys

from foodpass_desktop.main import main

if __name__ == "__main__":
    sys.exit(main())
