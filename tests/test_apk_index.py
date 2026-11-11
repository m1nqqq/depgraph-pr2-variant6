"""Тесты загрузки и разбора APKINDEX."""

import gzip
import tempfile
import unittest

from src.apk_index import (
    ApkIndex,
    load_index,
    parse_index,
    read_index_text,
    split_dependency,
)
from src.errors import RepositoryError
from tests.apk_fixture import INDEX_TEXT, make_archive, write_repository


class SplitDependencyTest(unittest.TestCase):
    """Тесты разбора записей зависимостей."""

    def test_plain_name(self):
        """Имя без ограничений."""
        self.assertEqual(split_dependency("musl"), "musl")

    def test_version_constraints(self):
        """Ограничения версий отбрасываются."""
        for token in ("lib>=1.0", "lib=1", "lib<2", "lib~3.1", "lib><1"):
            self.assertEqual(split_dependency(token), "lib")

    def test_virtual_names(self):
        """Виртуальные имена сохраняют префикс."""
        self.assertEqual(split_dependency("so:libc.so.6"), "so:libc.so.6")
        self.assertEqual(split_dependency("pc:zlib>=1.2"), "pc:zlib")

    def test_conflict_is_not_dependency(self):
        """Конфликты не считаются зависимостями."""
        self.assertIsNone(split_dependency("!other"))


class ParseIndexTest(unittest.TestCase):
    """Тесты разбора текста APKINDEX."""

    def test_records(self):
        """Читаются все записи с полями."""
        packages = parse_index(INDEX_TEXT)
        self.assertEqual(len(packages), 5)
        self.assertEqual(packages[0].name, "app")
        self.assertEqual(packages[0].version, "1.0-r0")
        self.assertIn("lib>=1.0", packages[0].depends)

    def test_record_without_dependencies(self):
        """Запись без поля D даёт пустой кортеж."""
        self.assertEqual(parse_index(INDEX_TEXT)[2].depends, ())

    def test_record_without_name(self):
        """Запись без P - ошибка репозитория."""
        with self.assertRaisesRegex(RepositoryError, "запись 1"):
            parse_index("V:1.0\nD:x\n")


class ReadIndexTextTest(unittest.TestCase):
    """Тесты чтения архива."""

    def test_two_part_archive(self):
        """Архив из подписи и данных читается целиком."""
        self.assertEqual(read_index_text(make_archive()), INDEX_TEXT)

    def test_not_gzip(self):
        """Произвольные байты не являются архивом."""
        with self.assertRaisesRegex(RepositoryError, "повреждён"):
            read_index_text(b"not an archive")

    def test_no_index_member(self):
        """В архиве нет файла APKINDEX."""
        data = gzip.compress(b"")
        with self.assertRaises(RepositoryError):
            read_index_text(data)


class ApkIndexTest(unittest.TestCase):
    """Тесты разрешения зависимостей."""

    @staticmethod
    def index():
        """Индекс из тестовых данных."""
        return ApkIndex(parse_index(INDEX_TEXT))

    def test_direct_dependencies_resolved(self):
        """Виртуальные имена заменяются пакетами-поставщиками."""
        names = self.index().direct_dependencies("app", "1.0-r0")
        self.assertEqual(names, ["lib", "musl", "tool"])

    def test_conflicts_and_self_skipped(self):
        """Конфликты и зависимость от самого себя пропускаются."""
        names = self.index().direct_dependencies("app", "1.0-r0")
        self.assertNotIn("conflict", names)
        self.assertNotIn("app", names)

    def test_other_version(self):
        """Выбирается запись нужной версии."""
        self.assertEqual(
            self.index().direct_dependencies("app", "0.9-r0"), []
        )

    def test_unknown_package(self):
        """Пакета нет в индексе."""
        with self.assertRaisesRegex(RepositoryError, "не найден"):
            self.index().find("nothing", "1")

    def test_unknown_version_lists_available(self):
        """При неверной версии показываются доступные."""
        with self.assertRaisesRegex(RepositoryError, "1.0-r0, 0.9-r0"):
            self.index().find("app", "9.9")

    def test_unresolved_name_kept(self):
        """Неразрешённое имя остаётся как есть."""
        self.assertEqual(self.index().resolve("so:libx.so"), "so:libx.so")


class LoadIndexTest(unittest.TestCase):
    """Тесты загрузки индекса по URL."""

    def test_load_from_file_url(self):
        """Индекс загружается по адресу file://."""
        with tempfile.TemporaryDirectory() as folder:
            index = load_index(write_repository(folder))
        self.assertIn("lib", index.by_name)

    def test_missing_archive(self):
        """Недоступный репозиторий - понятная ошибка."""
        with tempfile.TemporaryDirectory() as folder:
            url = "file://" + folder.replace("\\", "/") + "/none"
            with self.assertRaisesRegex(RepositoryError, "не удалось"):
                load_index(url)


if __name__ == "__main__":
    unittest.main()
