"""Вспомогательные средства для тестов."""

import os
import sys

SRC = os.path.join(os.path.dirname(os.path.dirname(__file__)), "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)


class Capture:
    """Собирает строки вывода эмулятора в список."""

    def __init__(self):
        """Создаёт пустой буфер."""
        self.lines = []

    def __call__(self, text=""):
        """Добавляет строку в буфер."""
        self.lines.append(str(text))

    @property
    def text(self):
        """Весь вывод одной строкой."""
        return "\n".join(self.lines)
