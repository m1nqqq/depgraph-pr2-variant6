"""Тесты сохранения изображения графа."""

import os
import tempfile
import unittest
from unittest import mock

from src.errors import RenderError
from src.file_repo import parse_test_repository
from src.graph import build_graph
from src.render import (
    RENDERER_BUILTIN,
    RENDERER_D2,
    d2_path_for,
    save_image,
)


def sample_graph():
    """Небольшой граф для проверок."""
    return build_graph(parse_test_repository("A: B\nB:\n"), "A")


class SaveImageTest(unittest.TestCase):
    """Тесты save_image."""

    def test_d2_path(self):
        """D2-файл лежит рядом с SVG."""
        self.assertEqual(d2_path_for("out.svg"), "out.d2")
        self.assertEqual(d2_path_for("a.b.svg"), "a.b.d2")

    def test_builtin_when_d2_missing(self):
        """Без утилиты d2 используется встроенная отрисовка."""
        with tempfile.TemporaryDirectory() as folder:
            svg = os.path.join(folder, "g.svg")
            with mock.patch("src.render.shutil.which", return_value=None):
                renderer = save_image(sample_graph(), svg)
            self.assertEqual(renderer, RENDERER_BUILTIN)
            self.assertTrue(os.path.isfile(svg))
            self.assertTrue(os.path.isfile(d2_path_for(svg)))

    def test_d2_used_when_available(self):
        """Если d2 отработала успешно, её результат сохраняется."""
        with tempfile.TemporaryDirectory() as folder:
            svg = os.path.join(folder, "g.svg")

            def fake_run(command, **_):
                """Имитирует d2: создаёт SVG-файл."""
                with open(command[2], "w", encoding="utf-8") as file:
                    file.write("<svg/>")
                return mock.Mock(returncode=0)

            with mock.patch("src.render.shutil.which", return_value="d2"):
                with mock.patch("src.render.subprocess.run", fake_run):
                    renderer = save_image(sample_graph(), svg)
            self.assertEqual(renderer, RENDERER_D2)
            with open(svg, encoding="utf-8") as file:
                self.assertEqual(file.read(), "<svg/>")

    def test_fallback_when_d2_fails(self):
        """Ошибка d2 не мешает получить SVG встроенным способом."""
        with tempfile.TemporaryDirectory() as folder:
            svg = os.path.join(folder, "g.svg")
            failed = mock.Mock(returncode=1)
            with mock.patch("src.render.shutil.which", return_value="d2"):
                with mock.patch(
                    "src.render.subprocess.run", return_value=failed
                ):
                    renderer = save_image(sample_graph(), svg)
            self.assertEqual(renderer, RENDERER_BUILTIN)
            self.assertTrue(os.path.isfile(svg))

    def test_write_error(self):
        """Невозможность записи файла - понятная ошибка."""
        with tempfile.TemporaryDirectory() as folder:
            svg = os.path.join(folder, "нет", "g.svg")
            with self.assertRaisesRegex(RenderError, "не удалось записать"):
                save_image(sample_graph(), svg)


if __name__ == "__main__":
    unittest.main()
