"""Права доступа узлов VFS: форматирование и разбор режимов chmod."""

import re

MODE_MASK = 0o777
DEFAULT_FILE_MODE = 0o644
DEFAULT_DIR_MODE = 0o755
OCTAL_RE = re.compile(r"[0-7]{1,4}")
CLAUSE_RE = re.compile(r"([ugoa]*)([-+=])([rwx]*)")
SHIFTS = {"u": 6, "g": 3, "o": 0}
BITS = {"r": 4, "w": 2, "x": 1}
FULL = 7
LETTERS = "rwx"


def format_mode(node):
    """Возвращает строку прав вида drwxr-xr-x."""
    text = "d" if node.is_dir else "-"
    for who in "ugo":
        triple = (node.mode >> SHIFTS[who]) & FULL
        text += "".join(letter if triple & BITS[letter] else "-"
                        for letter in LETTERS)
    return text


def parse_octal(text):
    """Разбирает восьмеричный режим (например, 755). Иначе None."""
    if not OCTAL_RE.fullmatch(text):
        return None
    return int(text, 8) & MODE_MASK


def _apply_clause(mode, who, op, perms):
    """Применяет одно символьное условие (например, g+w) к режиму."""
    bits = sum(BITS[letter] for letter in perms)
    for target in who or "ugo":
        targets = "ugo" if target == "a" else target
        for letter in targets:
            shift = SHIFTS[letter]
            if op == "=":
                mode &= ~(FULL << shift)
            if op == "-":
                mode &= ~(bits << shift)
            else:
                mode |= bits << shift
    return mode


def apply_mode(spec, mode):
    """Вычисляет новый режим по спецификации chmod.

    Поддерживаются восьмеричная запись (644) и символьная
    (u+x, go-w, a=r, u+rw,o-r). Неверная спецификация — ValueError.
    """
    octal = parse_octal(spec)
    if octal is not None:
        return octal
    for clause in spec.split(","):
        match = CLAUSE_RE.fullmatch(clause)
        if match is None:
            raise ValueError(spec)
        mode = _apply_clause(mode, *match.groups())
    return mode & MODE_MASK
