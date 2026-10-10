"""Виртуальная файловая система (VFS), полностью хранящаяся в памяти.

Источником VFS является XML-файл следующего вида::

    <vfs name="demo" home="/home/user">
      <dir name="home">
        <dir name="user">
          <file name="hello.txt">Hello!</file>
          <file name="logo.bin" encoding="base64">iVBORw0KGgo=</file>
        </dir>
      </dir>
    </vfs>

Каталоги задаются элементом ``dir``, файлы — элементом ``file``.
Двоичные данные хранятся в base64 (атрибут ``encoding="base64"``).
"""

import base64
import binascii
import os
import textwrap
import xml.etree.ElementTree as ET

ROOT_TAG = "vfs"
DIR_TAG = "dir"
FILE_TAG = "file"
SEPARATOR = "/"
FORBIDDEN_NAMES = ("", ".", "..")


class VFSError(Exception):
    """Ошибка загрузки VFS (файл не найден, неверный формат)."""


class Node:
    """Узел VFS: файл или каталог."""

    is_dir = False

    def __init__(self, name, parent=None):
        """Создаёт узел с именем name внутри каталога parent."""
        self.name = name
        self.parent = parent

    @property
    def path(self):
        """Абсолютный путь узла внутри VFS."""
        parts = []
        node = self
        while node.parent is not None:
            parts.append(node.name)
            node = node.parent
        return SEPARATOR + SEPARATOR.join(reversed(parts))


class File(Node):
    """Файл VFS; содержимое хранится в виде байтов."""

    def __init__(self, name, parent=None, data=b""):
        """Создаёт файл с содержимым data."""
        super().__init__(name, parent)
        self.data = data

    @property
    def size(self):
        """Размер файла в байтах."""
        return len(self.data)


class Directory(Node):
    """Каталог VFS; дочерние узлы хранятся в словаре по имени."""

    is_dir = True

    def __init__(self, name, parent=None):
        """Создаёт пустой каталог."""
        super().__init__(name, parent)
        self.children = {}

    def add(self, node):
        """Добавляет дочерний узел и возвращает его."""
        node.parent = self
        self.children[node.name] = node
        return node


class VFS:
    """Виртуальная файловая система: корень, имя и домашний каталог."""

    def __init__(self, name, root, home=SEPARATOR, source=None):
        """Создаёт VFS с корневым каталогом root."""
        self.name = name
        self.root = root
        self.home = home
        self.source = source

    def resolve(self, cwd, path):
        """Находит узел по абсолютному или относительному пути.

        Поддерживаются компоненты ``.``, ``..`` и ``~`` (домашний
        каталог). Возвращает None, если узел не найден.
        """
        if path == "~" or path.startswith("~" + SEPARATOR):
            node = self.resolve(self.root, self.home)
            path = path[1:]
        else:
            node = self.root if path.startswith(SEPARATOR) else cwd
        for part in path.split(SEPARATOR):
            if node is None or part in ("", "."):
                continue
            node = self._step(node, part)
        return node

    @staticmethod
    def _step(node, part):
        """Переходит из узла node к компоненту пути part."""
        if not node.is_dir:
            return None
        if part == "..":
            return node.parent if node.parent is not None else node
        return node.children.get(part)

    def stats(self):
        """Возвращает (число каталогов, число файлов, объём в байтах)."""
        dirs, files, total = 0, 0, 0
        stack = [self.root]
        while stack:
            node = stack.pop()
            if node.is_dir:
                dirs += 1
                stack.extend(node.children.values())
            else:
                files += 1
                total += node.size
        return dirs, files, total


def _decode_content(element):
    """Возвращает содержимое файла из XML-элемента в виде байтов."""
    text = element.text or ""
    if element.get("encoding") == "base64":
        try:
            return base64.b64decode("".join(text.split()), validate=True)
        except (binascii.Error, ValueError):
            raise VFSError(
                f"invalid base64 data in file '{element.get('name')}'"
            ) from None
    if text.startswith("\n"):
        text = textwrap.dedent(text).strip("\n") + "\n"
    return text.encode("utf-8")


def _check_name(element, directory):
    """Проверяет имя дочернего элемента и возвращает его."""
    name = element.get("name", "")
    if name in FORBIDDEN_NAMES or SEPARATOR in name:
        raise VFSError(f"invalid name '{name}' in <{element.tag}>")
    if name in directory.children:
        raise VFSError(f"duplicate name '{name}' in '{directory.path}'")
    return name


def _build(element, directory):
    """Рекурсивно заполняет каталог directory из XML-элемента."""
    for child in element:
        name = _check_name(child, directory)
        if child.tag == DIR_TAG:
            _build(child, directory.add(Directory(name)))
        elif child.tag == FILE_TAG:
            directory.add(File(name, data=_decode_content(child)))
        else:
            raise VFSError(f"unknown element <{child.tag}>")


def load_vfs(path):
    """Загружает VFS из XML-файла. Ошибки выбрасываются как VFSError."""
    try:
        tree = ET.parse(path)
    except FileNotFoundError:
        raise VFSError(f"VFS file not found: '{path}'") from None
    except OSError as error:
        raise VFSError(f"cannot read VFS '{path}': {error}") from None
    except ET.ParseError as error:
        raise VFSError(f"invalid XML in '{path}': {error}") from None
    element = tree.getroot()
    if element.tag != ROOT_TAG:
        raise VFSError(f"root element must be <{ROOT_TAG}>, "
                       f"got <{element.tag}>")
    root = Directory("")
    _build(element, root)
    default_name = os.path.splitext(os.path.basename(path))[0]
    vfs = VFS(element.get("name", default_name), root,
              element.get("home", SEPARATOR), source=path)
    home = vfs.resolve(root, vfs.home)
    if home is None or not home.is_dir:
        raise VFSError(f"home directory '{vfs.home}' does not exist")
    return vfs


def default_vfs():
    """Создаёт VFS по умолчанию в памяти."""
    root = Directory("")
    user = root.add(Directory("home")).add(Directory("user"))
    user.add(File("readme.txt", data=b"Default in-memory VFS\n"))
    etc = root.add(Directory("etc"))
    etc.add(File("hostname", data=b"emulator\n"))
    root.add(Directory("tmp"))
    return VFS("default", root, "/home/user")
