"""Тесты командной строки."""

import contextlib
import io
import os
import tempfile
import unittest
from unittest import mock

from src.main import EXIT_ERROR, EXIT_OK, main
from tests.apk_fixture import write_repository


def run_cli(*argv):
    """Запускает main, возвращает (код, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        with mock.patch("src.render.shutil.which", return_value=None):
            code = main(list(argv))
    return code, out.getvalue(), err.getvalue()


class CliTest(unittest.TestCase):
    """Сквозные тесты командной строки."""

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

    def test_prints_transitive_graph(self):
        """Выводится граф с транзитивными зависимостями."""
        with tempfile.TemporaryDirectory() as folder:
            code, out, _ = run_cli(self.make_config(folder))
        self.assertEqual(code, EXIT_OK)
        self.assertEqual(
            out.splitlines()[1:5],
            [
                "  app -> lib, musl, tool",
                "  lib -> musl",
                "  musl (нет зависимостей)",
                "  tool (нет зависимостей)",
            ],
        )

    def test_creates_d2_and_svg(self):
        """Создаются D2-описание и SVG."""
        with tempfile.TemporaryDirectory() as folder:
            code, out, _ = run_cli(self.make_config(folder))
            self.assertEqual(code, EXIT_OK)
            self.assertTrue(os.path.isfile(os.path.join(folder, "graph.svg")))
            self.assertTrue(os.path.isfile(os.path.join(folder, "graph.d2")))
        self.assertIn("Изображение (SVG, встроенный):", out)

    def test_reverse_mode_makes_no_image(self):
        """В режиме --reverse изображение не создаётся."""
        with tempfile.TemporaryDirectory() as folder:
            path = self.make_config(folder, package="musl", version="1.2-r0")
            run_cli(path, "--reverse")
            self.assertFalse(os.path.exists(os.path.join(folder, "graph.svg")))

    def test_no_dependencies(self):
        """Пакет без зависимостей."""
        with tempfile.TemporaryDirectory() as folder:
            path = self.make_config(folder, version="0.9-r0")
            code, out, _ = run_cli(path)
        self.assertEqual(code, EXIT_OK)
        self.assertIn("app (нет зависимостей)", out)

    def test_test_mode_cycle(self):
        """Тестовый режим показывает циклы."""
        with tempfile.TemporaryDirectory() as folder:
            repo = os.path.join(folder, "repo.txt")
            with open(repo, "w", encoding="utf-8") as file:
                file.write("A: B\nB: A\n")
            path = self.make_config(
                folder, package="A", repository=repo, test_mode="true"
            )
            code, out, _ = run_cli(path)
        self.assertEqual(code, EXIT_OK)
        self.assertIn("Циклические зависимости:", out)
        self.assertIn("  A -> B -> A", out)

    def test_test_mode_unknown_root(self):
        """Корневой пакет не описан в тестовом репозитории."""
        with tempfile.TemporaryDirectory() as folder:
            repo = os.path.join(folder, "repo.txt")
            with open(repo, "w", encoding="utf-8") as file:
                file.write("A: B\n")
            path = self.make_config(
                folder, package="Q", repository=repo, test_mode="true"
            )
            code, _, err = run_cli(path)
        self.assertEqual(code, EXIT_ERROR)
        self.assertIn("не описан", err)

    def test_broken_test_repository(self):
        """Синтаксическая ошибка в файле тестового репозитория."""
        with tempfile.TemporaryDirectory() as folder:
            repo = os.path.join(folder, "repo.txt")
            with open(repo, "w", encoding="utf-8") as file:
                file.write("A B\n")
            path = self.make_config(
                folder, package="A", repository=repo, test_mode="true"
            )
            code, _, err = run_cli(path)
        self.assertEqual(code, EXIT_ERROR)
        self.assertIn("строка 1", err)

    def test_reverse_mode_apk(self):
        """Режим --reverse для репозитория apk."""
        with tempfile.TemporaryDirectory() as folder:
            path = self.make_config(
                folder, package="musl", version="1.2-r0"
            )
            code, out, _ = run_cli(path, "--reverse")
        self.assertEqual(code, EXIT_OK)
        self.assertEqual(
            out.splitlines()[2:5],
            ["  app", "  lib", "Все, включая транзитивные:"],
        )

    def test_reverse_mode_test_repository(self):
        """Режим --reverse в тестовом режиме."""
        with tempfile.TemporaryDirectory() as folder:
            repo = os.path.join(folder, "repo.txt")
            with open(repo, "w", encoding="utf-8") as file:
                file.write("A: B\nB: C\nC:\n")
            path = self.make_config(
                folder, package="C", repository=repo, test_mode="true"
            )
            code, out, _ = run_cli(path, "--reverse")
        self.assertEqual(code, EXIT_OK)
        self.assertIn("Прямые (зависят от пакета напрямую):\n  B\n", out)

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
