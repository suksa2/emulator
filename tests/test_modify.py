"""Тесты команд chmod и cp и прав доступа (этап 5)."""

import os
import tempfile
import unittest

from tests.test_commands import DEEP, CommandTestCase
from emulator.perms import apply_mode, format_mode
from emulator.vfs import Directory, File, VFSError, load_vfs


class PermsTest(unittest.TestCase):
    """Разбор и форматирование режимов."""

    def test_octal(self):
        """Восьмеричная запись."""
        self.assertEqual(apply_mode("640", 0o777), 0o640)
        self.assertEqual(apply_mode("0755", 0), 0o755)

    def test_symbolic(self):
        """Символьная запись."""
        self.assertEqual(apply_mode("u+x", 0o644), 0o744)
        self.assertEqual(apply_mode("go-r", 0o644), 0o600)
        self.assertEqual(apply_mode("a=r", 0o777), 0o444)
        self.assertEqual(apply_mode("+x", 0o644), 0o755)
        self.assertEqual(apply_mode("u=rwx,g=,o-r", 0o644), 0o700)
        self.assertEqual(apply_mode("-w", 0o666), 0o444)

    def test_invalid(self):
        """Неверные режимы."""
        for spec in ("999", "u*x", "", "z+r", "u+q", "1234567"):
            with self.subTest(spec=spec):
                with self.assertRaises(ValueError):
                    apply_mode(spec, 0)

    def test_format(self):
        """Строка прав для ls -l."""
        self.assertEqual(format_mode(Directory("d")), "drwxr-xr-x")
        self.assertEqual(format_mode(File("f", mode=0o640)), "-rw-r-----")


class VfsModeTest(unittest.TestCase):
    """Атрибут mode в XML."""

    def test_mode_loaded(self):
        """Права из XML и значения по умолчанию."""
        vfs = load_vfs(DEEP)
        self.assertEqual(vfs.resolve(vfs.root, "/etc/hostname").mode, 0o600)
        self.assertEqual(vfs.resolve(vfs.root, "/etc/motd").mode, 0o644)
        self.assertEqual(vfs.resolve(vfs.root, "/etc").mode, 0o755)

    def test_bad_mode(self):
        """Неверный mode — ошибка загрузки."""
        handle, path = tempfile.mkstemp(suffix=".xml")
        with os.fdopen(handle, "w", encoding="utf-8") as file:
            file.write("<vfs><file name='a' mode='rw'/></vfs>")
        self.addCleanup(os.remove, path)
        with self.assertRaises(VFSError):
            load_vfs(path)


class ChmodTest(CommandTestCase):
    """chmod."""

    def mode(self, path):
        """Права узла."""
        return self.shell.vfs.resolve(self.shell.cwd, path).mode

    def test_modes(self):
        """Восьмеричный и символьный режим, -w как режим."""
        self.run_ok("chmod 600 notes.txt")
        self.assertEqual(self.mode("notes.txt"), 0o600)
        self.run_ok("chmod g+r,o+r notes.txt")
        self.assertEqual(self.mode("notes.txt"), 0o644)
        self.run_ok("chmod -w notes.txt")
        self.assertEqual(self.mode("notes.txt"), 0o444)
        self.assertIn("-r--r--r--", self.run_ok("ls -l"))

    def test_recursive_verbose(self):
        """-R применяет режим ко всем потомкам, -v сообщает о смене."""
        text = self.run_ok("chmod -Rv 700 projects")
        self.assertIn("changed from 0755 to 0700", text)
        self.assertEqual(self.mode("projects/app/assets/logo.png"), 0o700)

    def test_source_unchanged(self):
        """Изменения только в памяти."""
        self.run_ok("chmod 000 /etc/motd")
        vfs = load_vfs(DEEP)
        self.assertEqual(vfs.resolve(vfs.root, "/etc/motd").mode, 0o644)

    def test_errors(self):
        """Ошибки chmod."""
        self.assertIn("missing operand", self.run_fail("chmod"))
        self.assertIn("after '755'", self.run_fail("chmod 755"))
        self.assertIn("invalid mode", self.run_fail("chmod 8 notes.txt"))
        self.assertIn("No such file",
                      self.run_fail("chmod 600 /nope notes.txt"))
        self.assertEqual(self.mode("notes.txt"), 0o600)


class CpTest(CommandTestCase):
    """cp."""

    def node(self, path):
        """Узел по пути или None."""
        return self.shell.vfs.resolve(self.shell.cwd, path)

    def test_file_copy(self):
        """Копия файла независима от оригинала и сохраняет права."""
        self.run_ok("cp /etc/hostname copy")
        copy = self.node("copy")
        self.assertEqual(copy.data, b"emulator\n")
        self.assertEqual(copy.mode, 0o600)
        copy.data = b"changed"
        self.assertEqual(self.node("/etc/hostname").data, b"emulator\n")

    def test_into_directory(self):
        """Несколько источников в каталог, -v."""
        text = self.run_ok("cp -v /etc/motd notes.txt /tmp")
        self.assertIn("'notes.txt' -> '/tmp/notes.txt'", text)
        self.assertEqual(self.run_ok("ls /tmp"), "motd  notes.txt")

    def test_recursive(self):
        """Рекурсивное копирование и слияние каталогов."""
        self.assertIn("-r not specified", self.run_fail("cp projects /tmp"))
        self.run_ok("cp -r projects /tmp")
        self.assertIsNotNone(self.node("/tmp/projects/app/assets/logo.png"))
        self.run_ok("cp -R /etc /tmp/projects")
        self.run_ok("cp -r projects /tmp")
        self.assertIsNotNone(self.node("/tmp/projects/etc/motd"))
        self.run_ok("cp -r projects/app /tmp/renamed")
        self.assertEqual(self.run_ok("ls /tmp/renamed"), "assets  main.py")

    def test_errors(self):
        """Ошибки cp."""
        cases = {
            "cp": "missing file operand",
            "cp a": "missing destination",
            "cp /nope /tmp": "cannot stat",
            "cp notes.txt notes.txt": "same file",
            "cp -r projects projects/app": "into itself",
            "cp -r / /tmp": "into itself",
            "cp notes.txt /etc/motd /nope": "is not a directory",
            "cp notes.txt /no/dir/x": "No such file",
            "cp notes.txt newdir/": "Not a directory",
            "cp -r projects /etc/motd": "non-directory",
            "cp -x a b": "invalid option",
        }
        for line, message in cases.items():
            with self.subTest(line=line):
                self.assertIn(message, self.run_fail(line))


if __name__ == "__main__":
    unittest.main()
