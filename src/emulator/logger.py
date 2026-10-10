"""Журналирование вызовов команд в CSV-файл."""

import csv
import datetime
import os

FIELDS = ["timestamp", "user", "command", "args", "status", "message"]


class LogError(Exception):
    """Ошибка открытия лог-файла."""


class CommandLogger:
    """Записывает события вызова команд в CSV-файл (режим дозаписи)."""

    def __init__(self, path):
        """Открывает лог-файл; заголовок пишется в новый файл."""
        self.path = path
        try:
            is_new = not os.path.exists(path) or not os.path.getsize(path)
            self.file = open(path, "a", newline="", encoding="utf-8")
        except OSError as error:
            raise LogError(
                f"cannot open log file '{path}': {error.strerror}") from None
        self.writer = csv.writer(self.file)
        if is_new:
            self.writer.writerow(FIELDS)
            self.file.flush()

    def log(self, user, command, args, status, message=""):
        """Записывает одно событие вызова команды."""
        stamp = datetime.datetime.now().isoformat(timespec="seconds")
        self.writer.writerow(
            [stamp, user, command, " ".join(args), status, message])
        self.file.flush()

    def close(self):
        """Закрывает лог-файл."""
        self.file.close()
