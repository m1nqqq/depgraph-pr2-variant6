"""Тесты чтения и проверки конфигурации."""

import functools
import os
import tempfile
import unittest

from src.config import load_config, parse_yaml
from src.errors import ConfigError

TEST_REPO_TEXT = "A: B\nB:\n"


class ConfigTestCase(unittest.TestCase):
    """Базовый класс: временная папка с файлами."""

    @functools.cached_property
    def tmp(self):
        """Временная папка, удаляемая после теста."""
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        return folder

    @functools.cached_property
    def repo(self):
        """Путь к файлу тестового репозитория."""
        path = self.path("repo.txt")
        with open(path, "w", encoding="utf-8") as file:
            file.write(TEST_REPO_TEXT)
        return path

    def path(self, name):
        """Возвращает путь внутри временной папки."""
        return os.path.join(self.tmp.name, name)

    def write_config(self, **overrides):
        """Записывает конфигурацию с подменой отдельных параметров."""
        values = {
            "package": "A",
            "repository": self.repo,
            "test_mode": "true",
            "version": "1.0",
            "output_file": self.path("graph.svg"),
        }
        values.update(overrides)
        lines = [f"{key}: {value}" for key, value in values.items()]
        config_path = self.path("config.yaml")
        with open(config_path, "w", encoding="utf-8") as file:
            file.write("\n".join(lines) + "\n")
        return config_path


class ParseYamlTest(unittest.TestCase):
    """Тесты разбора YAML."""

    def test_comments_and_quotes(self):
        """Комментарии отбрасываются, кавычки снимаются."""
        text = "# заголовок\na: 'x # y'  # хвост\nb: \"z\"\n"
        self.assertEqual(parse_yaml(text), {"a": "x # y", "b": "z"})

    def test_url_value_keeps_colon(self):
        """Двоеточие внутри значения не ломает разбор."""
        result = parse_yaml("repository: https://host/path\n")
        self.assertEqual(result["repository"], "https://host/path")

    def test_duplicate_key(self):
        """Повторяющийся ключ - ошибка с номером строки."""
        with self.assertRaisesRegex(ConfigError, "строка 2"):
            parse_yaml("a: 1\na: 2\n")

    def test_bad_syntax(self):
        """Строка без двоеточия - ошибка."""
        with self.assertRaises(ConfigError):
            parse_yaml("просто текст\n")

    def test_nested_not_supported(self):
        """Вложенные структуры не поддерживаются."""
        with self.assertRaises(ConfigError):
            parse_yaml("a: 1\n  b: 2\n")


class LoadConfigTest(ConfigTestCase):
    """Тесты загрузки конфигурации."""

    def test_valid_config(self):
        """Корректная конфигурация читается целиком."""
        config = load_config(self.write_config())
        self.assertEqual(config.package, "A")
        self.assertTrue(config.test_mode)
        self.assertEqual(config.version, "1.0")

    def test_as_pairs_order(self):
        """Параметры выводятся в фиксированном порядке."""
        config = load_config(self.write_config())
        keys = [key for key, _ in config.as_pairs()]
        self.assertEqual(
            keys,
            ["package", "repository", "test_mode", "version", "output_file"],
        )

    def test_missing_file(self):
        """Отсутствующий файл конфигурации."""
        with self.assertRaisesRegex(ConfigError, "не найден"):
            load_config(self.path("нет.yaml"))

    def test_directory_instead_of_file(self):
        """Вместо файла передана папка."""
        with self.assertRaisesRegex(ConfigError, "папкой"):
            load_config(self.tmp.name)

    def test_missing_key(self):
        """Не задан обязательный параметр."""
        path = self.path("c.yaml")
        with open(path, "w", encoding="utf-8") as file:
            file.write("package: A\n")
        with self.assertRaisesRegex(ConfigError, "не заданы"):
            load_config(path)

    def test_unknown_key(self):
        """Лишний параметр."""
        path = self.write_config(extra="1")
        with self.assertRaisesRegex(ConfigError, "неизвестные"):
            load_config(path)

    def test_bad_bool(self):
        """Некорректное значение test_mode."""
        with self.assertRaisesRegex(ConfigError, "test_mode"):
            load_config(self.write_config(test_mode="maybe"))

    def test_empty_package(self):
        """Пустое имя пакета."""
        with self.assertRaisesRegex(ConfigError, "package"):
            load_config(self.write_config(package=""))

    def test_test_mode_package_must_be_capital(self):
        """В тестовом режиме имя пакета - большие латинские буквы."""
        with self.assertRaisesRegex(ConfigError, "большие латинские"):
            load_config(self.write_config(package="abc"))

    def test_real_mode_package_name(self):
        """В обычном режиме имя пакета проверяется по правилам apk."""
        path = self.write_config(
            test_mode="false",
            repository="https://example.org/main/x86_64",
            package="bad name!",
        )
        with self.assertRaisesRegex(ConfigError, "package"):
            load_config(path)

    def test_repository_file_missing(self):
        """Файл тестового репозитория не существует."""
        path = self.write_config(repository=self.path("нет.txt"))
        with self.assertRaisesRegex(ConfigError, "repository"):
            load_config(path)

    def test_repository_must_be_url(self):
        """В обычном режиме нужен URL."""
        path = self.write_config(test_mode="false", repository="/tmp/x")
        with self.assertRaisesRegex(ConfigError, "URL"):
            load_config(path)

    def test_bad_version(self):
        """Некорректная версия."""
        with self.assertRaisesRegex(ConfigError, "version"):
            load_config(self.write_config(version="abc"))

    def test_output_must_be_svg(self):
        """Расширение выходного файла должно быть .svg."""
        path = self.write_config(output_file=self.path("graph.png"))
        with self.assertRaisesRegex(ConfigError, "svg"):
            load_config(path)

    def test_output_directory_missing(self):
        """Папка для выходного файла не существует."""
        path = self.write_config(output_file=self.path("x/y/g.svg"))
        with self.assertRaisesRegex(ConfigError, "папка"):
            load_config(path)


if __name__ == "__main__":
    unittest.main()
