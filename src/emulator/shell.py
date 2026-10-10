"""Ядро эмулятора: выполнение команд независимо от интерфейса."""

import getpass
import socket

from emulator.commands import COMMANDS
from emulator.errors import ExitRequest, ShellError
from emulator.parser import parse
from emulator.vfs import SEPARATOR, default_vfs

COMMENT = "#"


def strip_comment(line):
    """Удаляет комментарий в стиле Python (# до конца строки)."""
    return line.split(COMMENT, 1)[0].rstrip()


class Shell:
    """Командная оболочка эмулятора."""

    def __init__(self, vfs=None, output=print, logger=None):
        """Создаёт оболочку над VFS.

        Если VFS не передана, создаётся VFS по умолчанию в памяти.
        output — функция вывода строки, logger — CommandLogger или None.
        """
        self.output = output
        self.logger = logger
        self.user = getpass.getuser()
        self.host = socket.gethostname()
        self.vfs = vfs if vfs is not None else default_vfs()
        self.cwd = self.vfs.resolve(self.vfs.root, self.vfs.home)

    def title(self):
        """Заголовок окна на основе данных ОС."""
        return f"Эмулятор - [{self.user}@{self.host}]"

    def display_path(self):
        """Текущий путь для приглашения; домашний каталог — ~."""
        path, home = self.cwd.path, self.vfs.home
        if home == SEPARATOR:
            return path
        if path == home:
            return "~"
        if path.startswith(home + SEPARATOR):
            return "~" + path[len(home):]
        return path

    def prompt(self):
        """Приглашение к вводу вида user@host:~$ ."""
        return f"{self.user}@{self.host}:{self.display_path()}$ "

    def execute(self, line):
        """Выполняет одну строку. Ошибки выбрасываются как ShellError."""
        name, args = parse(line)
        if name is None:
            return
        handler = COMMANDS.get(name)
        try:
            if handler is None:
                raise ShellError(f"{name}: command not found")
            handler(self, args)
        except ShellError as error:
            self._log(name, args, "error", str(error))
            raise
        except ExitRequest as request:
            self._log(name, args, "exit", str(request.code))
            raise
        self._log(name, args, "ok")

    def _log(self, name, args, status, message=""):
        """Записывает событие вызова команды в лог, если он задан."""
        if self.logger is not None:
            self.logger.log(self.user, name, args, status, message)

    def run_line(self, line):
        """Выполняет строку и сообщает об ошибке. Возвращает успех."""
        try:
            self.execute(line)
        except ShellError as error:
            self.output(f"error: {error}")
            return False
        return True

    def run_script(self, path):
        """Выполняет стартовый скрипт построчно.

        Поддерживаются комментарии # (синтаксис Python), в том числе в
        конце строки. Ввод и вывод отображаются как диалог; об ошибке
        сообщается с номером строки. Возвращает число ошибок.
        """
        try:
            with open(path, encoding="utf-8-sig") as file:
                lines = file.read().splitlines()
        except OSError as error:
            raise ShellError(
                f"cannot read script '{path}': {error.strerror}") from None
        failed = 0
        for number, raw in enumerate(lines, start=1):
            line = strip_comment(raw)
            if not line.strip():
                continue
            self.output(self.prompt() + line)
            if not self.run_line(line):
                failed += 1
                self.output(f"[script] error at {path}:{number}")
        return failed
