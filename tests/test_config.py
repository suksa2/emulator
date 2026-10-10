"""Тесты параметров, лога CSV и стартового скрипта (этап 2)."""

import csv
import os
import tempfile
import unittest

from tests.helpers import Capture
from emulator.config import dump_config, parse_args
from emulator.errors import ExitRequest, ShellError
from emulator.logger import FIELDS, CommandLogger, LogError
from emulator.shell import Shell, strip_comment


class TempDirTestCase(unittest.TestCase):
    """Базовый класс с временным каталогом."""

    def setUp(self):
        """Создаёт временный каталог."""
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def path(self, name):
        """Путь к файлу во временном каталоге."""
        return os.path.join(self.tmp.name, name)


class ConfigTest(unittest.TestCase):
    """Проверка разбора параметров."""

    def test_defaults(self):
        """Без параметров значения не заданы."""
        config = parse_args([])
        self.assertEqual((config.vfs, config.log, config.script),
                         (None, None, None))
        self.assertFalse(config.no_gui)

    def test_all_options(self):
        """Все параметры разбираются и выводятся."""
        config = parse_args(["--vfs", "a.xml", "--log", "l.csv",
                             "--script", "s.txt", "--no-gui"])
        out = Capture()
        dump_config(config, out)
        for expected in ("vfs = a.xml", "log = l.csv", "script = s.txt",
                         "no_gui = True"):
            self.assertIn(expected, out.text)


class LoggerTest(TempDirTestCase):
    """Проверка CSV-лога."""

    def read_rows(self, name):
        """Читает строки CSV-файла."""
        with open(self.path(name), newline="", encoding="utf-8") as file:
            return list(csv.reader(file))

    def test_events_logged(self):
        """Каждый вызов команды записывается с датой, временем и именем."""
        logger = CommandLogger(self.path("log.csv"))
        shell = Shell(output=Capture(), logger=logger)
        shell.run_line("ls -a b")
        shell.run_line("nope")
        with self.assertRaises(ExitRequest):
            shell.execute("exit 2")
        logger.close()
        rows = self.read_rows("log.csv")
        self.assertEqual(rows[0], FIELDS)
        self.assertEqual(rows[1][1:5], [shell.user, "ls", "-a b", "ok"])
        self.assertRegex(rows[1][0], r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d$")
        self.assertEqual(rows[2][4], "error")
        self.assertEqual(rows[3][4:], ["exit", "2"])

    def test_append_without_second_header(self):
        """Повторное открытие дописывает без нового заголовка."""
        for _ in range(2):
            logger = CommandLogger(self.path("log.csv"))
            logger.log("u", "ls", [], "ok")
            logger.close()
        self.assertEqual(len(self.read_rows("log.csv")), 3)

    def test_bad_path(self):
        """Ошибка открытия лог-файла."""
        with self.assertRaises(LogError):
            CommandLogger(self.path("missing_dir/log.csv"))


class ScriptTest(TempDirTestCase):
    """Проверка выполнения стартового скрипта."""

    def setUp(self):
        """Создаёт оболочку."""
        super().setUp()
        self.out = Capture()
        self.shell = Shell(output=self.out)

    def write(self, text):
        """Записывает скрипт и возвращает путь."""
        with open(self.path("s.txt"), "w", encoding="utf-8") as file:
            file.write(text)
        return self.path("s.txt")

    def test_comments(self):
        """Комментарии # целиком и в конце строки."""
        self.assertEqual(strip_comment("cd a  # go"), "cd a")
        path = self.write("# head\nls x # tail\n   # only\n")
        self.assertEqual(self.shell.run_script(path), 0)
        self.assertEqual(self.out.lines,
                         [self.shell.prompt() + "ls x", "ls: args=['x']"])

    def test_errors_reported(self):
        """Об ошибке сообщается с номером строки."""
        path = self.write("ls\nbad\nexit x\n")
        self.assertEqual(self.shell.run_script(path), 2)
        self.assertIn(f"error at {path}:2", self.out.text)
        self.assertIn(f"error at {path}:3", self.out.text)

    def test_missing_script(self):
        """Отсутствующий скрипт — ошибка."""
        with self.assertRaises(ShellError):
            self.shell.run_script(self.path("none.txt"))


if __name__ == "__main__":
    unittest.main()
