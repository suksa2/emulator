"""Тесты ядра оболочки (этап 1)."""

import unittest

from tests.helpers import Capture
from emulator.errors import ExitRequest
from emulator.shell import Shell


class ShellTest(unittest.TestCase):
    """Проверка выполнения команд и сообщений об ошибках."""

    def setUp(self):
        """Создаёт оболочку с перехватом вывода."""
        self.out = Capture()
        self.shell = Shell(output=self.out)

    def test_title_uses_os_data(self):
        """Заголовок окна содержит имя пользователя и хоста."""
        self.assertEqual(self.shell.title(),
                         f"Эмулятор - [{self.shell.user}@{self.shell.host}]")

    def test_stub_commands(self):
        """Заглушки выводят имя и аргументы."""
        self.assertTrue(self.shell.run_line("ls -l docs"))
        self.assertTrue(self.shell.run_line("cd /tmp"))
        self.assertEqual(self.out.lines,
                         ["ls: args=['-l', 'docs']", "cd: args=['/tmp']"])

    def test_unknown_command(self):
        """Неизвестная команда — сообщение об ошибке."""
        self.assertFalse(self.shell.run_line("foo bar"))
        self.assertIn("foo: command not found", self.out.text)

    def test_empty_line(self):
        """Пустая строка ничего не делает."""
        self.assertTrue(self.shell.run_line("   "))
        self.assertEqual(self.out.lines, [])

    def test_exit(self):
        """exit выбрасывает запрос на выход с кодом."""
        with self.assertRaises(ExitRequest) as context:
            self.shell.execute("exit 4")
        self.assertEqual(context.exception.code, 4)

    def test_exit_bad_args(self):
        """Неверные аргументы exit."""
        self.assertFalse(self.shell.run_line("exit abc"))
        self.assertFalse(self.shell.run_line("exit 1 2"))
        self.assertIn("numeric argument required", self.out.text)
        self.assertIn("too many arguments", self.out.text)


if __name__ == "__main__":
    unittest.main()
