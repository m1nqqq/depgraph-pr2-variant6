"""Тесты построения графа обходом в глубину."""

import unittest

from src.file_repo import parse_test_repository
from src.graph import build_graph, format_cycles, format_graph
from src.repo import DictRepository

CHAIN_LENGTH = 5000


def graph_of(text, root="A"):
    """Строит граф по тексту тестового репозитория."""
    return build_graph(parse_test_repository(text), root)


class BuildGraphTest(unittest.TestCase):
    """Тесты build_graph."""

    def test_single_package(self):
        """Пакет без зависимостей."""
        graph = graph_of("A:\n")
        self.assertEqual(graph.edges, {"A": []})
        self.assertEqual(graph.cycles, [])

    def test_transitive_dependencies(self):
        """Транзитивные зависимости попадают в граф."""
        graph = graph_of("A: B\nB: C\nC: D\nD:\n")
        self.assertEqual(list(graph.edges), ["A", "B", "C", "D"])

    def test_diamond_visits_shared_node_once(self):
        """Общая зависимость обходится один раз."""
        graph = graph_of("A: B C\nB: D\nC: D\nD:\n")
        self.assertEqual(list(graph.edges), ["A", "B", "D", "C"])
        self.assertEqual(graph.cycles, [])

    def test_dfs_order(self):
        """Порядок обнаружения соответствует обходу в глубину."""
        graph = graph_of("A: B C\nB: D\nC: E\nD:\nE:\n")
        self.assertEqual(list(graph.edges), ["A", "B", "D", "C", "E"])

    def test_unreachable_packages_ignored(self):
        """Недостижимые из корня пакеты не включаются."""
        graph = graph_of("A: B\nB:\nX: A\n")
        self.assertNotIn("X", graph.edges)

    def test_simple_cycle(self):
        """Простой цикл находится и не приводит к зависанию."""
        graph = graph_of("A: B\nB: C\nC: A\n")
        self.assertEqual(graph.cycles, [["A", "B", "C", "A"]])
        self.assertEqual(graph.edges["C"], ["A"])

    def test_self_dependency(self):
        """Зависимость пакета от самого себя."""
        graph = graph_of("A: A B\nB:\n")
        self.assertEqual(graph.cycles, [["A", "A"]])

    def test_cycle_not_through_root(self):
        """Цикл, не содержащий корень."""
        graph = graph_of("A: B\nB: C\nC: B\n")
        self.assertEqual(graph.cycles, [["B", "C", "B"]])

    def test_several_cycles(self):
        """Несколько циклов в одном графе."""
        graph = graph_of("A: B C\nB: A\nC: C\n")
        self.assertEqual(len(graph.cycles), 2)

    def test_deep_chain_without_recursion(self):
        """Глубокая цепочка не вызывает переполнения стека."""
        edges = {f"P{i}": [f"P{i + 1}"] for i in range(CHAIN_LENGTH)}
        edges[f"P{CHAIN_LENGTH}"] = []
        graph = build_graph(DictRepository(edges), "P0")
        self.assertEqual(len(graph.edges), CHAIN_LENGTH + 1)


class FormatTest(unittest.TestCase):
    """Тесты текстового вывода."""

    def test_format_graph(self):
        """Строки графа."""
        lines = format_graph(graph_of("A: B\nB:\n"))
        self.assertEqual(lines, ["A -> B", "B (нет зависимостей)"])

    def test_format_cycles(self):
        """Строки циклов."""
        lines = format_cycles(graph_of("A: B\nB: A\n"))
        self.assertEqual(lines, ["  A -> B -> A"])


if __name__ == "__main__":
    unittest.main()
