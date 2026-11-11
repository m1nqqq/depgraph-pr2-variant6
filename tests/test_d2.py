"""Тесты D2-представления графа."""

import unittest

from src.d2 import quote, to_d2
from src.file_repo import parse_test_repository
from src.graph import build_graph
from src.repo import DictRepository


def d2_of(text, root="A"):
    """D2-текст графа тестового репозитория."""
    return to_d2(build_graph(parse_test_repository(text), root))


class QuoteTest(unittest.TestCase):
    """Тесты экранирования имён."""

    def test_plain(self):
        """Имя берётся в двойные кавычки."""
        self.assertEqual(quote("nginx"), '"nginx"')

    def test_dots_and_colons_stay_inside_quotes(self):
        """Точки и двоеточия не должны превращаться в синтаксис D2."""
        self.assertEqual(quote("python3.12"), '"python3.12"')
        self.assertEqual(quote("so:libc.so.6"), '"so:libc.so.6"')

    def test_escaping(self):
        """Кавычки и обратная косая черта экранируются."""
        self.assertEqual(quote('a"b\\c'), '"a\\"b\\\\c"')


class ToD2Test(unittest.TestCase):
    """Тесты генерации D2."""

    def test_header_and_edges(self):
        """Есть направление и рёбра."""
        text = d2_of("A: B C\nB:\nC:\n")
        self.assertTrue(text.startswith("direction: right\n"))
        self.assertIn('"A" -> "B"\n', text)
        self.assertIn('"A" -> "C"\n', text)

    def test_leaf_declared(self):
        """Вершина без зависимостей объявляется отдельно."""
        text = d2_of("A: B\nB:\n")
        self.assertIn('\n"B"\n', text)

    def test_root_highlighted(self):
        """Корневая вершина подсвечена."""
        text = d2_of("A: B\nB:\n")
        self.assertIn('"A": {\n  style: {\n    fill: "#ffe699"', text)
        self.assertNotIn('"B": {', text)

    def test_cycle_edge_marked(self):
        """Ребро, замыкающее цикл, рисуется пунктиром."""
        text = d2_of("A: B\nB: A\n")
        self.assertIn('"B" -> "A": {', text)
        self.assertIn("stroke-dash: 3", text)
        self.assertNotIn('"A" -> "B": {', text)

    def test_self_loop(self):
        """Самозависимость выводится ребром в ту же вершину."""
        text = d2_of("A: A\n")
        self.assertIn('"A" -> "A": {', text)

    def test_real_package_names(self):
        """Имена реальных пакетов apk корректно экранируются."""
        repo = DictRepository({"python3.12": ["libstdc++"], "libstdc++": []})
        text = to_d2(build_graph(repo, "python3.12"))
        self.assertIn('"python3.12" -> "libstdc++"', text)

    def test_ends_with_newline(self):
        """Текст оканчивается переводом строки."""
        self.assertTrue(d2_of("A:\n").endswith("\n"))


if __name__ == "__main__":
    unittest.main()
