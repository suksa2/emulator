"""Тесты загрузки VFS из XML (этап 3)."""

import os
import tempfile
import unittest

from tests.helpers import Capture
from emulator.shell import Shell
from emulator.vfs import VFSError, default_vfs, load_vfs

EXAMPLES = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "examples", "vfs")


def example(name):
    """Путь к файлу примера VFS."""
    return os.path.join(EXAMPLES, name)


class LoadTest(unittest.TestCase):
    """Проверка загрузки примеров VFS."""

    def test_minimal(self):
        """Минимальная VFS содержит только корень."""
        vfs = load_vfs(example("minimal.xml"))
        self.assertEqual(vfs.name, "minimal")
        self.assertEqual(vfs.stats(), (1, 0, 0))

    def test_several_files(self):
        """Текстовые и двоичные файлы загружаются в память."""
        vfs = load_vfs(example("several_files.xml"))
        data = vfs.resolve(vfs.root, "/data.bin").data
        self.assertEqual(data, bytes(range(10)))
        colors = vfs.resolve(vfs.root, "colors.txt").data.decode()
        self.assertTrue(colors.startswith("red\nred\n"))

    def test_deep(self):
        """Глубокая вложенность и разрешение путей."""
        vfs = load_vfs(example("deep.xml"))
        node = vfs.resolve(vfs.root, "~/projects/app/assets/logo.png")
        self.assertEqual(node.path, "/home/user/projects/app/assets/logo.png")
        self.assertTrue(node.data.startswith(b"\x89PNG"))
        app = vfs.resolve(vfs.root, "/home/user/projects/app")
        self.assertIs(vfs.resolve(app, "../../.."), vfs.resolve(
            vfs.root, "/home"))
        self.assertIs(vfs.resolve(vfs.root, "/../.."), vfs.root)

    def test_missing_nodes(self):
        """Несуществующие пути и путь через файл дают None."""
        vfs = load_vfs(example("deep.xml"))
        self.assertIsNone(vfs.resolve(vfs.root, "/nope"))
        self.assertIsNone(vfs.resolve(vfs.root, "/etc/motd/x"))

    def test_errors(self):
        """Ошибки загрузки: нет файла, неверный XML, неверный base64."""
        for name in ("missing.xml", "broken.xml", "bad_base64.xml"):
            with self.subTest(name=name):
                with self.assertRaises(VFSError):
                    load_vfs(example(name))

    def test_wrong_structure(self):
        """Неверный корневой тег, дубликаты и неизвестные элементы."""
        bodies = ["<root/>",
                  "<vfs><file name='a'/><file name='a'/></vfs>",
                  "<vfs><link name='a'/></vfs>",
                  "<vfs><dir name='..'/></vfs>",
                  "<vfs home='/nope'/>"]
        for body in bodies:
            with self.subTest(body=body):
                with self.assertRaises(VFSError):
                    load_vfs(self.temp_xml(body))

    def temp_xml(self, body):
        """Создаёт временный XML-файл и возвращает путь к нему."""
        handle, path = tempfile.mkstemp(suffix=".xml")
        with os.fdopen(handle, "w", encoding="utf-8") as file:
            file.write(body)
        self.addCleanup(os.remove, path)
        return path


class ShellVfsTest(unittest.TestCase):
    """Проверка связи оболочки и VFS."""

    def test_default_vfs(self):
        """Без пути создаётся VFS по умолчанию, cwd — домашний каталог."""
        out = Capture()
        shell = Shell(output=out)
        self.assertEqual(shell.vfs.name, default_vfs().name)
        self.assertEqual(shell.cwd.path, "/home/user")
        self.assertTrue(shell.prompt().endswith(":~$ "))
        shell.run_line("vfs-info")
        self.assertIn("in-memory default", out.text)

    def test_prompt_outside_home(self):
        """Вне домашнего каталога выводится полный путь."""
        shell = Shell(load_vfs(example("deep.xml")), output=Capture())
        shell.cwd = shell.vfs.resolve(shell.vfs.root, "/var/log")
        self.assertTrue(shell.prompt().endswith(":/var/log$ "))
        shell.cwd = shell.vfs.resolve(shell.vfs.root, "~/projects")
        self.assertTrue(shell.prompt().endswith(":~/projects$ "))


if __name__ == "__main__":
    unittest.main()
