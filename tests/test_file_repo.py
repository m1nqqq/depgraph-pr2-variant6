"""Тесты тестового репозитория из файла."""

import os
import tempfile
import unittest

from src.errors import RepositoryError
from src.file_repo import load_test_repository, parse_test_repository


class ParseTestRepositoryTest(unittest.TestCase):
    """Тесты разбора описания графа."""

    def test_basic(self):
        """Читаются зависимости и пустые списки."""
        repo = parse_test_repository("A: B C\nB:\nC: B\n")
        self.assertEqual(repo.dependencies("A"), ["B", "C"])
        self.assertEqual(repo.dependencies("B"), [])
        self.assertEqual(repo.dependencies("C"), ["B"])

    def test_comments_and_blank_lines(self):
        """Комментарии и пустые строки пропускаются."""
        repo = parse_test_repository("# шапка\n\nA: B  # хвост\n")
        self.assertEqual(repo.dependencies("A"), ["B"])

    def test_duplicate_dependencies_removed(self):
        """Повторы в списке зависимостей убираются."""
        repo = parse_test_repository("A: B B C\n")
        self.assertEqual(repo.dependencies("A"), ["B", "C"])

    def test_unknown_package_has_no_dependencies(self):
        """Пакет, не описанный ключом, считается листом."""
        repo = parse_test_repository("A: Z\n")
        self.assertEqual(repo.dependencies("Z"), [])

    def test_duplicate_package(self):
        """Повторное описание пакета - ошибка."""
        with self.assertRaisesRegex(RepositoryError, "строка 2"):
            parse_test_repository("A: B\nA: C\n")

    def test_lowercase_rejected(self):
        """Имена должны быть большими латинскими буквами."""
        with self.assertRaises(RepositoryError):
            parse_test_repository("a: B\n")
        with self.assertRaisesRegex(RepositoryError, "недопустимое"):
            parse_test_repository("A: b\n")

    def test_syntax_error(self):
        """Строка без двоеточия - ошибка."""
        with self.assertRaisesRegex(RepositoryError, "строка 1"):
            parse_test_repository("A B\n")

    def test_require(self):
        """Корневой пакет должен быть описан."""
        repo = parse_test_repository("A: B\n")
        repo.require("A")
        with self.assertRaisesRegex(RepositoryError, "'Q'"):
            repo.require("Q")


class LoadTestRepositoryTest(unittest.TestCase):
    """Тесты чтения файла."""

    def test_missing_file(self):
        """Отсутствующий файл."""
        with self.assertRaisesRegex(RepositoryError, "не удалось"):
            load_test_repository("нет_такого_файла.txt")

    def test_read_file(self):
        """Файл читается целиком."""
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "repo.txt")
            with open(path, "w", encoding="utf-8") as file:
                file.write("A: B\n")
            repo = load_test_repository(path)
        self.assertEqual(repo.dependencies("A"), ["B"])


if __name__ == "__main__":
    unittest.main()
