"""Тесты парсера."""

import unittest

from tests.helpers import SRC  # noqa: F401
from emulator.parser import parse


class ParserTest(unittest.TestCase):
    """Проверка разбиения строки на команду и аргументы."""

    def test_empty(self):
        """Пустая строка не содержит команды."""
        self.assertEqual(parse("   "), (None, []))

    def test_command_only(self):
        """Строка из одной команды."""
        self.assertEqual(parse("ls"), ("ls", []))

    def test_args_split_by_spaces(self):
        """Аргументы разделяются любым числом пробелов."""
        self.assertEqual(parse("  cd   a  b "), ("cd", ["a", "b"]))


if __name__ == "__main__":
    unittest.main()
