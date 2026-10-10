"""Реализация команд эмулятора."""

from emulator.errors import ExitRequest, ShellError

MAX_EXIT_ARGS = 1


def cmd_ls(shell, args):
    """Заглушка ls: выводит имя команды и аргументы."""
    shell.output(f"ls: args={args}")


def cmd_cd(shell, args):
    """Заглушка cd: выводит имя команды и аргументы."""
    shell.output(f"cd: args={args}")


def cmd_exit(shell, args):
    """Завершает работу эмулятора: exit [код]."""
    if len(args) > MAX_EXIT_ARGS:
        raise ShellError("exit: too many arguments")
    if not args:
        raise ExitRequest(0)
    try:
        code = int(args[0])
    except ValueError:
        raise ShellError(
            f"exit: {args[0]}: numeric argument required") from None
    raise ExitRequest(code)


COMMANDS = {
    "ls": cmd_ls,
    "cd": cmd_cd,
    "exit": cmd_exit,
}
