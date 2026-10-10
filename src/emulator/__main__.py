"""Точка входа: python -m emulator [--vfs] [--log] [--script] [--no-gui]."""

import sys

from emulator.config import dump_config, parse_args
from emulator.errors import ExitRequest, ShellError
from emulator.logger import CommandLogger, LogError
from emulator.shell import Shell
from emulator.vfs import VFSError, default_vfs, load_vfs

STARTUP_DELAY_MS = 100


def build_shell(config):
    """Создаёт оболочку по параметрам; ошибки — ShellError."""
    try:
        vfs = load_vfs(config.vfs) if config.vfs else default_vfs()
    except VFSError as error:
        raise ShellError(f"VFS load failed: {error}") from None
    try:
        logger = CommandLogger(config.log) if config.log else None
    except LogError as error:
        raise ShellError(str(error)) from None
    return Shell(vfs, logger=logger)


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


def show_error_window(message):
    """Показывает ошибку запуска в диалоговом окне."""
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Эмулятор", message)
        root.destroy()
    except Exception:  # noqa: BLE001 - нет дисплея: достаточно консоли
        pass


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
        if not config.no_gui:
            show_error_window(str(error))
        return 1


if __name__ == "__main__":
    sys.exit(main())
