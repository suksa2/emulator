"""Точка входа: python -m emulator."""

import sys

from emulator.gui import EmulatorApp
from emulator.shell import Shell


def main():
    """Открывает окно эмулятора."""
    return EmulatorApp(Shell()).run()


if __name__ == "__main__":
    sys.exit(main())
