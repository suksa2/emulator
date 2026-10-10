"""Тесты графического интерфейса (пропускаются без дисплея)."""

import tkinter as tk
import unittest

from tests.helpers import SRC  # noqa: F401
from emulator.gui import EmulatorApp
from emulator.shell import Shell


class GuiTest(unittest.TestCase):
    """Проверка окна эмулятора без запуска главного цикла."""

    def setUp(self):
        """Создаёт скрытое окно."""
        try:
            root = tk.Tk()
        except tk.TclError as error:
            self.skipTest(f"no display: {error}")
        root.withdraw()
        self.shell = Shell()
        self.app = EmulatorApp(self.shell, root)
        self.closed = False

    def tearDown(self):
        """Закрывает окно, если оно ещё открыто."""
        if not self.closed:
            self.app.root.destroy()

    def text(self):
        """Содержимое области вывода."""
        return self.app.text.get("1.0", "end")

    def test_title(self):
        """Заголовок окна формируется из данных ОС."""
        self.assertEqual(self.app.root.title(), self.shell.title())

    def test_dialog(self):
        """Ввод отображается вместе с приглашением и выводом."""
        self.app.entry.insert(0, "whoami")
        self.app.on_enter()
        self.app.submit("nope")
        text = self.text()
        self.assertIn(self.shell.prompt() + "whoami", text)
        self.assertIn(f"\n{self.shell.user}\n", text)
        self.assertIn("error: nope: command not found", text)
        self.assertEqual(self.app.entry.get(), "")

    def test_history(self):
        """Стрелка вверх возвращает предыдущую команду."""
        for line in ("cd a", "cd b"):
            self.app.entry.insert(0, line)
            self.app.on_enter()
        self.app._browse(-1)
        self.assertEqual(self.app.entry.get(), "cd b")
        self.app._browse(-1)
        self.assertEqual(self.app.entry.get(), "cd a")

    def test_exit_closes_window(self):
        """exit закрывает окно с кодом возврата."""
        self.app.submit("exit 3")
        self.closed = True
        self.assertEqual(self.app.exit_code, 3)


if __name__ == "__main__":
    unittest.main()
