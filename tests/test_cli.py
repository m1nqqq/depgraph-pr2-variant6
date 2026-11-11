"""Тесты командной строки."""

import contextlib
import io
import os
import tempfile
import unittest

from src.main import EXIT_ERROR, EXIT_OK, main
from tests.apk_fixture import write_repository


def run_cli(*argv):
    """Запускает main, возвращает (код, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = main(list(argv))
    return code, out.getvalue(), err.getvalue()


class CliTest(unittest.TestCase):
    """Сквозные тесты этапа 2."""

    def make_config(self, folder, **overrides):
        """Создаёт конфигурацию для файлового репозитория."""
        values = {
            "package": "app",
            "repository": write_repository(folder),
            "test_mode": "false",
            "version": "1.0-r0",
            "output_file": os.path.join(folder, "graph.svg"),
        }
        values.update(overrides)
        path = os.path.join(folder, "config.yaml")
        with open(path, "w", encoding="utf-8") as file:
            for key, value in values.items():
                file.write(f"{key}: {value}\n")
        return path

    def test_prints_direct_dependencies(self):
        """Выводятся прямые зависимости."""
        with tempfile.TemporaryDirectory() as folder:
            code, out, _ = run_cli(self.make_config(folder))
        self.assertEqual(code, EXIT_OK)
        self.assertEqual(
            out.splitlines()[1:], ["  lib", "  musl", "  tool"]
        )

    def test_no_dependencies(self):
        """Пакет без зависимостей."""
        with tempfile.TemporaryDirectory() as folder:
            path = self.make_config(folder, version="0.9-r0")
            code, out, _ = run_cli(path)
        self.assertEqual(code, EXIT_OK)
        self.assertIn("(нет зависимостей)", out)

    def test_wrong_version(self):
        """Неверная версия даёт код ошибки и подсказку."""
        with tempfile.TemporaryDirectory() as folder:
            code, _, err = run_cli(self.make_config(folder, version="9"))
        self.assertEqual(code, EXIT_ERROR)
        self.assertIn("доступны", err)

    def test_config_error(self):
        """Ошибка конфигурации не приводит к трассировке."""
        code, _, err = run_cli("нет_такого.yaml")
        self.assertEqual(code, EXIT_ERROR)
        self.assertTrue(err.startswith("Ошибка:"))


if __name__ == "__main__":
    unittest.main()
