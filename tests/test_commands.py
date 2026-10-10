"""Тесты основных команд: ls, cd, whoami, uniq, uptime (этап 4)."""

import os
import unittest

from tests.helpers import Capture
from emulator.commands import _format_duration, _pretty_duration
from emulator.shell import Shell
from emulator.vfs import load_vfs

DEEP = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                    "examples", "vfs", "deep.xml")


class CommandTestCase(unittest.TestCase):
    """Базовый класс: оболочка над deep.xml с перехватом вывода."""

    def setUp(self):
        """Создаёт оболочку."""
        self.out = Capture()
        self.shell = Shell(load_vfs(DEEP), output=self.out)

    def run_ok(self, line):
        """Выполняет команду, ожидая успех, и возвращает её вывод."""
        self.out.lines.clear()
        self.assertTrue(self.shell.run_line(line), self.out.text)
        return self.out.text

    def run_fail(self, line):
        """Выполняет команду, ожидая ошибку, и возвращает вывод."""
        self.out.lines.clear()
        self.assertFalse(self.shell.run_line(line), self.out.text)
        return self.out.text


class LsCdWhoamiTest(CommandTestCase):
    """ls, cd, whoami."""

    def test_whoami(self):
        """whoami выводит имя пользователя ОС и не принимает аргументов."""
        self.assertEqual(self.run_ok("whoami"), self.shell.user)
        self.assertIn("extra operand", self.run_fail("whoami x"))

    def test_ls_default(self):
        """ls без аргументов выводит отсортированное содержимое."""
        self.assertEqual(self.run_ok("ls"), "notes.txt  projects")
        self.assertEqual(self.run_ok("ls -a"),
                         ".  ..  notes.txt  projects")

    def test_ls_long_and_multiple(self):
        """ls -l и несколько путей."""
        text = self.run_ok("ls -l /etc")
        self.assertIn("-rw-r--r--", text)
        self.assertIn("motd", text)
        text = self.run_ok("ls /etc /tmp")
        self.assertIn("/etc:", text)
        self.assertEqual(self.run_ok("ls /tmp"), "")
        self.assertEqual(self.run_ok("ls /etc/motd"), "motd")

    def test_ls_errors(self):
        """ls для несуществующего пути и неверной опции."""
        self.assertIn("cannot access", self.run_fail("ls /nope /etc"))
        self.assertIn("hostname", self.out.text)
        self.assertIn("invalid option", self.run_fail("ls -z"))

    def test_cd(self):
        """cd: относительные, абсолютные пути, домой, назад."""
        self.run_ok("cd projects/app/assets")
        self.assertEqual(self.shell.cwd.path,
                         "/home/user/projects/app/assets")
        self.run_ok("cd ../..")
        self.assertEqual(self.shell.cwd.path, "/home/user/projects")
        self.run_ok("cd /var/log")
        self.assertEqual(self.run_ok("cd -"), "/home/user/projects")
        self.run_ok("cd")
        self.assertEqual(self.shell.cwd.path, "/home/user")

    def test_cd_errors(self):
        """Ошибки cd."""
        self.assertIn("Not a directory", self.run_fail("cd /etc/motd"))
        self.assertIn("No such file", self.run_fail("cd /none"))
        self.assertIn("too many", self.run_fail("cd a b"))
        self.assertIn("OLDPWD", self.run_fail("cd -"))
        self.assertEqual(self.shell.cwd.path, "/home/user")


class UniqTest(CommandTestCase):
    """uniq."""

    def test_plain(self):
        """Соседние повторы схлопываются."""
        self.assertEqual(self.run_ok("uniq /var/log/system.log"),
                         "boot ok\ndisk warning\nnetwork up")

    def test_options(self):
        """Опции -c, -d, -u, -i."""
        log = "/var/log/system.log"
        self.assertIn("      3 disk warning", self.run_ok(f"uniq -c {log}"))
        self.assertEqual(self.run_ok(f"uniq -d {log}"),
                         "boot ok\ndisk warning")
        self.assertEqual(self.run_ok(f"uniq -u {log}"), "network up")
        text = self.run_ok("uniq -ic notes.txt")
        self.assertIn("      2 call mom", text)
        self.assertIn("      1 buy milk", text)

    def test_errors(self):
        """Ошибки uniq."""
        self.assertIn("missing file", self.run_fail("uniq"))
        self.assertIn("Is a directory", self.run_fail("uniq /etc"))
        self.assertIn("No such file", self.run_fail("uniq nope"))
        self.assertIn("extra operand", self.run_fail("uniq a b"))
        self.assertIn("invalid option", self.run_fail("uniq -x notes.txt"))


class UptimeTest(CommandTestCase):
    """uptime."""

    def test_modes(self):
        """Обычный вывод, -p и -s."""
        self.assertIn("up 0 min,  1 user", self.run_ok("uptime"))
        self.assertEqual(self.run_ok("uptime -p"), "up 0 minutes")
        self.assertRegex(self.run_ok("uptime -s"),
                         r"^\d{4}-\d\d-\d\d \d\d:\d\d:\d\d$")

    def test_errors(self):
        """Лишние аргументы и неверная опция."""
        self.run_fail("uptime now")
        self.run_fail("uptime -q")

    def test_formatting(self):
        """Форматирование длительности."""
        self.assertEqual(_format_duration(125), "2 min")
        self.assertEqual(_format_duration(3 * 3600 + 300), "3:05")
        self.assertEqual(_format_duration(86400 + 60), "1 day, 1 min")
        self.assertEqual(_format_duration(2 * 86400), "2 days, 0 min")
        self.assertEqual(_pretty_duration(3660), "up 1 hour, 1 minute")


if __name__ == "__main__":
    unittest.main()
