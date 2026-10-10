"""Команды, изменяющие VFS в памяти: chmod и cp."""

from emulator.errors import ShellError
from emulator.options import split_options
from emulator.perms import apply_mode
from emulator.vfs import SEPARATOR

SINGLE = 1
MIN_CHMOD_OPERANDS = 2
CHMOD_OPTIONS = "Rv"


def _walk(node):
    """Перебирает узел и всех его потомков."""
    yield node
    if node.is_dir:
        for child in list(node.children.values()):
            yield from _walk(child)


def _chmod_one(shell, spec, path, flags):
    """Меняет права одного пути; возвращает сообщение об ошибке или None."""
    node = shell.vfs.resolve(shell.cwd, path)
    if node is None:
        return f"cannot access '{path}': No such file or directory"
    targets = _walk(node) if "R" in flags else [node]
    for target in targets:
        old = target.mode
        target.mode = apply_mode(spec, old)
        if "v" in flags:
            shell.output(f"mode of '{target.path}' changed from "
                         f"{old:04o} to {target.mode:04o}")
    return None


def _chmod_split(args):
    """Отделяет опции -R/-v от операндов.

    Как в GNU chmod, аргумент вида -x или -w считается режимом.
    """
    flags, operands = set(), []
    for arg in args:
        letters = set(arg[1:])
        if (not operands and arg.startswith("-") and letters
                and letters <= set(CHMOD_OPTIONS)):
            flags |= letters
        else:
            operands.append(arg)
    return flags, operands


def cmd_chmod(shell, args):
    """chmod [-R] [-v] РЕЖИМ путь...: меняет права доступа (в памяти).

    РЕЖИМ — восьмеричный (755) или символьный (u+x, go-w, a=r,u+w, -x).
    """
    flags, operands = _chmod_split(args)
    if not operands:
        raise ShellError("chmod: missing operand")
    if len(operands) < MIN_CHMOD_OPERANDS:
        raise ShellError(f"chmod: missing operand after '{operands[0]}'")
    spec, paths = operands[0], operands[1:]
    try:
        apply_mode(spec, 0)
    except ValueError:
        raise ShellError(f"chmod: invalid mode: '{spec}'") from None
    errors = [error for error in
              (_chmod_one(shell, spec, path, flags) for path in paths)
              if error]
    if errors:
        raise ShellError("; ".join(f"chmod: {error}" for error in errors))


def _is_inside(node, ancestor):
    """Проверяет, что node совпадает с ancestor или вложен в него."""
    while node is not None:
        if node is ancestor:
            return True
        node = node.parent
    return False


def _split_path(path):
    """Делит путь на (каталог, имя)."""
    head, sep, name = path.rstrip(SEPARATOR).rpartition(SEPARATOR)
    if not sep:
        return ".", name
    return head or SEPARATOR, name


def _target(shell, source, dest, dest_node):
    """Определяет (каталог назначения, имя копии) для cp."""
    if dest_node is not None and dest_node.is_dir:
        return dest_node, source.name
    if dest.endswith(SEPARATOR):
        raise ShellError(f"cannot create '{dest}': Not a directory")
    head, name = _split_path(dest)
    parent = shell.vfs.resolve(shell.cwd, head)
    if parent is None or not parent.is_dir:
        raise ShellError(
            f"cannot create '{dest}': No such file or directory")
    return parent, name


def _check_copy(source, existing, parent, names):
    """Проверяет допустимость копирования source в parent."""
    src, dest = names
    if source.is_dir and _is_inside(parent, source):
        raise ShellError(f"cannot copy a directory, '{src}', "
                         f"into itself, '{dest}'")
    if existing is source:
        raise ShellError(f"'{src}' and '{dest}' are the same file")
    if existing is None or existing.is_dir == source.is_dir:
        return
    if existing.is_dir:
        raise ShellError(f"cannot overwrite directory '{dest}' "
                         "with non-directory")
    raise ShellError(f"cannot overwrite non-directory '{dest}' "
                     f"with directory '{src}'")


def _merge(source, target):
    """Копирует содержимое каталога source в существующий target."""
    for name, child in source.children.items():
        existing = target.children.get(name)
        if existing is not None and existing.is_dir != child.is_dir:
            raise ShellError(f"cannot overwrite '{existing.path}': "
                             "type mismatch")
        if child.is_dir and existing is not None:
            _merge(child, existing)
        else:
            target.add(child.clone(name))


def _cp_one(shell, src, dest, dest_node, flags):
    """Копирует один источник; ошибки — ShellError."""
    source = shell.vfs.resolve(shell.cwd, src)
    if source is None:
        raise ShellError(f"cannot stat '{src}': No such file or directory")
    if source.is_dir and "r" not in flags:
        raise ShellError(f"-r not specified; omitting directory '{src}'")
    parent, name = _target(shell, source, dest, dest_node)
    existing = parent.children.get(name)
    _check_copy(source, existing, parent, (src, dest))
    if source.is_dir and existing is not None:
        _merge(source, existing)
    else:
        parent.add(source.clone(name))
    if "v" in flags:
        shell.output(f"'{src}' -> '{parent.children[name].path}'")


def _collect(shell, sources, dest, dest_node, flags):
    """Копирует все источники и возвращает список ошибок."""
    errors = []
    for src in sources:
        try:
            _cp_one(shell, src, dest, dest_node, flags)
        except ShellError as error:
            errors.append(f"cp: {error}")
    return errors


def cmd_cp(shell, args):
    """cp [-r|-R] [-v] ИСТОЧНИК... НАЗНАЧЕНИЕ: копирует (в памяти)."""
    flags, operands = split_options("cp", args, "rRv")
    if "R" in flags:
        flags.add("r")
    if not operands:
        raise ShellError("cp: missing file operand")
    if len(operands) == SINGLE:
        raise ShellError(
            f"cp: missing destination file operand after '{operands[0]}'")
    sources, dest = operands[:-1], operands[-1]
    dest_node = shell.vfs.resolve(shell.cwd, dest)
    is_dir = dest_node is not None and dest_node.is_dir
    if len(sources) > SINGLE and not is_dir:
        raise ShellError(f"cp: target '{dest}' is not a directory")
    errors = _collect(shell, sources, dest, dest_node, flags)
    if errors:
        raise ShellError("; ".join(errors))
