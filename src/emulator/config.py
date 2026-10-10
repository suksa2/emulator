"""Разбор параметров командной строки эмулятора."""

import argparse


def build_arg_parser():
    """Создаёт парсер параметров командной строки."""
    parser = argparse.ArgumentParser(
        prog="emulator",
        description="Эмулятор командной оболочки UNIX-подобной ОС (GUI).")
    parser.add_argument(
        "--vfs", metavar="PATH", default=None,
        help="путь к физическому расположению VFS (XML-файл)")
    parser.add_argument(
        "--log", metavar="PATH", default=None,
        help="путь к лог-файлу вызовов команд (CSV)")
    parser.add_argument(
        "--script", metavar="PATH", default=None,
        help="путь к стартовому скрипту")
    parser.add_argument(
        "--no-gui", action="store_true",
        help="выполнить скрипт в консоли без окна (для автотестов)")
    return parser


def parse_args(argv=None):
    """Разбирает параметры командной строки."""
    return build_arg_parser().parse_args(argv)


def dump_config(config, output):
    """Отладочный вывод всех заданных параметров эмулятора."""
    output("[config] Параметры эмулятора:")
    for key, value in sorted(vars(config).items()):
        shown = value if value is not None else "<не задан>"
        output(f"[config]   {key} = {shown}")
