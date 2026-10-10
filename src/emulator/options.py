"""Разбор коротких опций команд (например, -l, -cd)."""

from emulator.errors import ShellError

OPTION_PREFIX = "-"
END_OF_OPTIONS = "--"


def split_options(command, args, allowed):
    """Разделяет аргументы на множество опций и список операндов.

    Опции — односимвольные флаги, которые можно объединять (-la).
    Аргумент ``--`` завершает список опций; одиночный ``-`` считается
    операндом. Неизвестная опция вызывает ShellError.
    """
    flags, operands = set(), []
    parsing = True
    for arg in args:
        if parsing and arg == END_OF_OPTIONS:
            parsing = False
        elif parsing and arg.startswith(OPTION_PREFIX) and arg != "-":
            flags.update(_check_flags(command, arg[1:], allowed))
        else:
            operands.append(arg)
    return flags, operands


def _check_flags(command, letters, allowed):
    """Проверяет, что все буквы опций допустимы, и возвращает их."""
    for letter in letters:
        if letter not in allowed:
            raise ShellError(f"{command}: invalid option -- '{letter}'")
    return set(letters)
