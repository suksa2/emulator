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


def cmd_vfs_info(shell, args):
    """Служебная команда: сведения о загруженной VFS."""
    if args:
        raise ShellError("vfs-info: too many arguments")
    vfs = shell.vfs
    dirs, files, total = vfs.stats()
    shell.output(f"name: {vfs.name}")
    shell.output(f"source: {vfs.source or '<in-memory default>'}")
    shell.output(f"home: {vfs.home}")
    shell.output(f"directories: {dirs}, files: {files}, bytes: {total}")


COMMANDS = {
    "ls": cmd_ls,
    "cd": cmd_cd,
    "exit": cmd_exit,
    "vfs-info": cmd_vfs_info,
}
