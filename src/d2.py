"""Текстовое представление графа зависимостей на языке диаграмм D2."""

ROOT_FILL = "#ffe699"
CYCLE_COLOR = "#cc0000"
CYCLE_DASH = 3
INDENT = "  "


def quote(name):
    """Возвращает имя в двойных кавычках с экранированием."""
    escaped = name.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def back_edges(graph):
    """Рёбра, замыкающие циклы (последнее ребро каждого цикла)."""
    return {(cycle[-2], cycle[-1]) for cycle in graph.cycles}


def _node_lines(name, is_root):
    """Объявление вершины; корневая подсвечивается цветом."""
    if not is_root:
        return [quote(name)]
    return [
        f"{quote(name)}: {{",
        f"{INDENT}style: {{",
        f'{INDENT * 2}fill: "{ROOT_FILL}"',
        f"{INDENT}}}",
        "}",
    ]


def _edge_lines(source, target, is_cycle):
    """Объявление ребра; рёбра циклов рисуются красным пунктиром."""
    edge = f"{quote(source)} -> {quote(target)}"
    if not is_cycle:
        return [edge]
    return [
        f"{edge}: {{",
        f"{INDENT}style: {{",
        f'{INDENT * 2}stroke: "{CYCLE_COLOR}"',
        f"{INDENT * 2}stroke-dash: {CYCLE_DASH}",
        f"{INDENT}}}",
        "}",
    ]


def to_d2(graph):
    """Формирует D2-описание графа: вершины, затем рёбра."""
    lines = ["direction: right", ""]
    for name in graph.edges:
        lines.extend(_node_lines(name, name == graph.root))
    lines.append("")
    cycle_edges = back_edges(graph)
    for source, targets in graph.edges.items():
        for target in targets:
            is_cycle = (source, target) in cycle_edges
            lines.extend(_edge_lines(source, target, is_cycle))
    return "\n".join(lines) + "\n"
