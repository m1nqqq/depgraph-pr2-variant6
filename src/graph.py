"""Построение графа зависимостей обходом в глубину (без рекурсии)."""

from dataclasses import dataclass, field


@dataclass
class Graph:
    """Граф зависимостей: рёбра в порядке обнаружения и найденные циклы."""

    root: str
    edges: dict = field(default_factory=dict)
    cycles: list = field(default_factory=list)


def _cycle_path(stack, child):
    """Возвращает цикл ``child -> ... -> child`` по текущему пути обхода."""
    path = [node for node, _ in stack]
    return path[path.index(child):] + [child]


def build_graph(repo, root):
    """Строит граф зависимостей пакета с учётом транзитивности.

    Итеративный DFS: явный стек пар (вершина, итератор по потомкам).
    Ребро в вершину, лежащую на текущем пути, образует цикл: оно
    сохраняется в графе и в списке циклов, но вершина повторно
    не раскрывается, поэтому обход всегда завершается.
    """
    graph = Graph(root=root)
    graph.edges[root] = repo.dependencies(root)
    stack = [(root, iter(graph.edges[root]))]
    on_path = {root}
    while stack:
        node, children = stack[-1]
        child = next(children, None)
        if child is None:
            stack.pop()
            on_path.discard(node)
        elif child in on_path:
            graph.cycles.append(_cycle_path(stack, child))
        elif child not in graph.edges:
            graph.edges[child] = repo.dependencies(child)
            stack.append((child, iter(graph.edges[child])))
            on_path.add(child)
    return graph


def format_graph(graph):
    """Возвращает текстовое представление графа списком строк."""
    lines = []
    for node, dependencies in graph.edges.items():
        if dependencies:
            lines.append(f"{node} -> {', '.join(dependencies)}")
        else:
            lines.append(f"{node} (нет зависимостей)")
    return lines


def format_cycles(graph):
    """Возвращает строки с описанием найденных циклов."""
    return ["  " + " -> ".join(cycle) for cycle in graph.cycles]
