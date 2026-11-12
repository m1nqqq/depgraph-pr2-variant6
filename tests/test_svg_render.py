"""Тесты встроенной отрисовки SVG."""

import unittest
import xml.etree.ElementTree as element_tree

from src.file_repo import parse_test_repository
from src.graph import build_graph
from src.repo import DictRepository
from src.svg_render import layout, render_svg

NAMESPACE = "{http://www.w3.org/2000/svg}"


def svg_of(text, root="A"):
    """Разбирает SVG, построенный для тестового репозитория."""
    graph = build_graph(parse_test_repository(text), root)
    return element_tree.fromstring(render_svg(graph))


def edge_paths(tree):
    """Пути рёбер (элементы path с маркером стрелки)."""
    return [
        item for item in tree.iter(f"{NAMESPACE}path")
        if item.get("marker-end")
    ]


class RenderSvgTest(unittest.TestCase):
    """Тесты render_svg."""

    def test_valid_xml(self):
        """SVG - корректный XML с корневым элементом svg."""
        tree = svg_of("A: B C\nB: C\nC:\n")
        self.assertEqual(tree.tag, f"{NAMESPACE}svg")

    def test_node_and_edge_counts(self):
        """Число вершин и рёбер совпадает с графом."""
        tree = svg_of("A: B C\nB: C\nC:\n")
        texts = [item.text for item in tree.iter(f"{NAMESPACE}text")]
        self.assertEqual(sorted(texts), ["A", "B", "C"])
        self.assertEqual(len(edge_paths(tree)), 3)

    def test_cycle_edges_dashed(self):
        """Рёбра циклов - пунктирные."""
        tree = svg_of("A: B\nB: A\n")
        dashed = [
            item for item in edge_paths(tree)
            if item.get("stroke-dasharray")
        ]
        self.assertEqual(len(dashed), 1)

    def test_self_loop_has_path(self):
        """Самозависимость рисуется петлёй."""
        tree = svg_of("A: A\n")
        self.assertEqual(len(edge_paths(tree)), 1)
        self.assertNotIn("nan", edge_paths(tree)[0].get("d").lower())

    def test_names_are_escaped(self):
        """Спецсимволы в именах не ломают XML."""
        graph = build_graph(DictRepository({"a&b": ["<c>"]}), "a&b")
        tree = element_tree.fromstring(render_svg(graph))
        texts = [item.text for item in tree.iter(f"{NAMESPACE}text")]
        self.assertEqual(sorted(texts), ["<c>", "a&b"])


class LayoutTest(unittest.TestCase):
    """Тесты раскладки."""

    def test_levels_left_to_right(self):
        """Зависимости располагаются правее зависящих."""
        graph = build_graph(parse_test_repository("A: B\nB: C\nC:\n"), "A")
        positions, _, _ = layout(graph)
        self.assertLess(positions["A"][0], positions["B"][0])
        self.assertLess(positions["B"][0], positions["C"][0])

    def test_nodes_do_not_overlap(self):
        """Вершины одной колонки не пересекаются по вертикали."""
        graph = build_graph(parse_test_repository("A: B C D\n"), "A")
        positions, _, _ = layout(graph)
        ys = sorted(positions[name][1] for name in "BCD")
        self.assertEqual(len(set(ys)), len(ys))


if __name__ == "__main__":
    unittest.main()
