"""Точка входа: python -m emulator [--vfs] [--log] [--script] [--no-gui]."""

import sys

from emulator.config import dump_config, parse_args
from emulator.errors import ExitRequest, ShellError
from emulator.logger import CommandLogger, LogError
from emulator.shell import Shell

STARTUP_DELAY_MS = 100


def build_shell(config):
    """Создаёт оболочку по параметрам; ошибки — ShellError."""
    try:
        logger = CommandLogger(config.log) if config.log else None
    except LogError as error:
        raise ShellError(str(error)) from None
    return Shell(logger=logger)


def run_script_safely(shell, path):
    """Выполняет стартовый скрипт и сообщает о его ошибках."""
    try:
        failed = shell.run_script(path)
    except ShellError as error:
        shell.output(f"error: {error}")
        return
    if failed:
        shell.output(f"[script] finished with {failed} error(s)")


def run_console(shell, config):
    """Консольный режим: выполняет скрипт без окна."""
    if config.script:
        run_script_safely(shell, config.script)
    return 0


def build_app(argv=None):
    """Создаёт окно эмулятора и планирует запуск стартового скрипта."""
    from emulator.gui import EmulatorApp
    config = parse_args(argv)
    shell = build_shell(config)
    app = EmulatorApp(shell)
    dump_config(config, shell.output)
    if config.script:
        app.root.after(STARTUP_DELAY_MS, app.guarded, run_script_safely,
                       shell, config.script)
    return app


def main(argv=None):
    """Запускает эмулятор в графическом или консольном режиме."""
    config = parse_args(argv)
    dump_config(config, print)
    try:
        if config.no_gui:
            return run_console(build_shell(config), config)
        return build_app(argv).run()
    except ExitRequest as request:
        return request.code
    except ShellError as error:
        print(f"error: {error}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
