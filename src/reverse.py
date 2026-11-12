"""Обратные зависимости: какие пакеты зависят от заданного."""

from dataclasses import dataclass, field

from src.graph import build_graph
from src.repo import DictRepository


@dataclass
class Dependents:
    """Пакеты, зависящие от заданного, и найденные циклы."""

    package: str
    direct: list = field(default_factory=list)
    transitive: list = field(default_factory=list)
    cycles: list = field(default_factory=list)


def reverse_repository(repo):
    """Строит репозиторий с обращёнными рёбрами «зависит от»."""
    reversed_edges = {name: [] for name in repo.names()}
    for name in repo.names():
        for dependency in repo.dependencies(name):
            reversed_edges.setdefault(dependency, []).append(name)
    return DictRepository(reversed_edges)


def find_dependents(repo, package):
    """Находит пакеты, зависящие от package прямо и транзитивно.

    Используется тот же итеративный обход в глубину, что и для прямого
    графа, но на репозитории с обращёнными рёбрами.
    """
    graph = build_graph(reverse_repository(repo), package)
    return Dependents(
        package=package,
        direct=[name for name in graph.edges[package] if name != package],
        transitive=[name for name in graph.edges if name != package],
        cycles=[list(reversed(cycle)) for cycle in graph.cycles],
    )


def format_dependents(result):
    """Возвращает строки отчёта об обратных зависимостях."""
    lines = [f"Обратные зависимости пакета {result.package}:"]
    if not result.transitive:
        return lines + ["  (от пакета никто не зависит)"]
    lines.append("Прямые (зависят от пакета напрямую):")
    lines.extend(f"  {name}" for name in result.direct)
    lines.append("Все, включая транзитивные:")
    lines.extend(f"  {name}" for name in result.transitive)
    return lines
