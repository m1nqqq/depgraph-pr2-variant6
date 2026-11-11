"""Тесты обратных зависимостей."""

import unittest

from src.file_repo import parse_test_repository
from src.reverse import (
    find_dependents,
    format_dependents,
    reverse_repository,
)

DIAMOND = "A: B C\nB: D\nC: D\nD:\nX: A\n"


def dependents_of(text, package):
    """Обратные зависимости пакета в тестовом репозитории."""
    return find_dependents(parse_test_repository(text), package)


class ReverseRepositoryTest(unittest.TestCase):
    """Тесты обращения рёбер."""

    def test_edges_reversed(self):
        """Рёбра меняют направление."""
        repo = reverse_repository(parse_test_repository("A: B C\nB: C\n"))
        self.assertEqual(repo.dependencies("C"), ["A", "B"])
        self.assertEqual(repo.dependencies("B"), ["A"])
        self.assertEqual(repo.dependencies("A"), [])

    def test_names_include_leaves(self):
        """Пакеты, упомянутые только как зависимости, не теряются."""
        repo = parse_test_repository("A: Z\n")
        self.assertEqual(repo.names(), ["A", "Z"])


class FindDependentsTest(unittest.TestCase):
    """Тесты поиска зависящих пакетов."""

    def test_direct_and_transitive(self):
        """Прямые и транзитивные обратные зависимости."""
        result = dependents_of(DIAMOND, "D")
        self.assertEqual(result.direct, ["B", "C"])
        self.assertEqual(sorted(result.transitive), ["A", "B", "C", "X"])

    def test_nobody_depends(self):
        """Корень, от которого никто не зависит."""
        result = dependents_of(DIAMOND, "X")
        self.assertEqual(result.direct, [])
        self.assertEqual(result.transitive, [])

    def test_middle_package(self):
        """Пакет в середине цепочки."""
        result = dependents_of(DIAMOND, "B")
        self.assertEqual(result.direct, ["A"])
        self.assertEqual(result.transitive, ["A", "X"])

    def test_cycle_in_forward_direction(self):
        """Цикл выводится в направлении «зависит от»."""
        result = dependents_of("A: B\nB: A\n", "A")
        self.assertEqual(result.direct, ["B"])
        self.assertEqual(result.cycles, [["A", "B", "A"]])

    def test_package_is_not_its_own_dependent(self):
        """Сам пакет не попадает в списки зависящих."""
        result = dependents_of("A: A B\nB:\n", "A")
        self.assertEqual(result.direct, [])
        self.assertEqual(result.cycles, [["A", "A"]])


class FormatDependentsTest(unittest.TestCase):
    """Тесты вывода."""

    def test_empty(self):
        """Сообщение, когда зависящих пакетов нет."""
        lines = format_dependents(dependents_of(DIAMOND, "X"))
        self.assertEqual(
            lines,
            [
                "Обратные зависимости пакета X:",
                "  (от пакета никто не зависит)",
            ],
        )

    def test_sections(self):
        """Выводятся прямые и все зависящие пакеты."""
        lines = format_dependents(dependents_of(DIAMOND, "B"))
        self.assertEqual(lines[1], "Прямые (зависят от пакета напрямую):")
        self.assertIn("Все, включая транзитивные:", lines)


if __name__ == "__main__":
    unittest.main()
