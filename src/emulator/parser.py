"""Простой парсер строки ввода."""

BOM = "﻿"


def parse(line):
    """Разделяет строку на команду и аргументы по пробелам.

    Возвращает кортеж (команда, список аргументов). Для пустой строки
    команда равна None.
    """
    parts = line.replace(BOM, "").split()
    if not parts:
        return None, []
    return parts[0], parts[1:]
