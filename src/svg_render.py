"""Встроенная отрисовка графа в SVG (запасной вариант без утилиты d2)."""

from collections import deque
from xml.sax.saxutils import escape

from src.d2 import back_edges

NODE_HEIGHT = 36
CHAR_WIDTH = 8
NODE_PAD = 24
MIN_WIDTH = 60
GAP_X = 90
GAP_Y = 44
MARGIN = 30
ARC = 45
LOOP = 16
SELF_ARC = 26
ROOT_FILL = "#ffe699"
NODE_FILL = "#e8f0fe"
EDGE_COLOR = "#555555"
CYCLE_COLOR = "#cc0000"
SVG_HEADER = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
    'viewBox="0 0 {w} {h}" font-family="sans-serif" font-size="14">'
)
ARROW = (
    '<defs><marker id="arrow-{kind}" viewBox="0 0 10 10" refX="9" '
    'refY="5" markerWidth="8" markerHeight="8" orient="auto">'
    '<path d="M0,0 L10,5 L0,10 z" fill="{color}"/></marker></defs>'
)


def _levels(graph):
    """Номер уровня каждой вершины: расстояние от корня (BFS)."""
    levels = {graph.root: 0}
    queue = deque([graph.root])
    while queue:
        node = queue.popleft()
        for child in graph.edges[node]:
            if child not in levels:
                levels[child] = levels[node] + 1
                queue.append(child)
    return levels


def _node_width(name):
    """Ширина прямоугольника вершины по длине имени."""
    return max(MIN_WIDTH, len(name) * CHAR_WIDTH + NODE_PAD)


def _column_height(count):
    """Высота колонки из count вершин."""
    return count * (NODE_HEIGHT + GAP_Y) - GAP_Y


def _place_column(names, left, total_height):
    """Размещает вершины одной колонки; возвращает позиции и ширину."""
    widths = [_node_width(name) for name in names]
    column_width = max(widths)
    offset = (total_height - _column_height(len(names))) / 2
    top = MARGIN + ARC + offset
    positions = {}
    for row, (name, width) in enumerate(zip(names, widths)):
        center_y = top + row * (NODE_HEIGHT + GAP_Y) + NODE_HEIGHT / 2
        positions[name] = (left + column_width / 2, center_y, width)
    return positions, column_width


def layout(graph):
    """Раскладывает вершины по колонкам-уровням.

    Возвращает (позиции {имя: (x, y, ширина)}, ширина, высота холста).
    """
    columns = {}
    for name, level in _levels(graph).items():
        columns.setdefault(level, []).append(name)
    total_height = _column_height(max(map(len, columns.values())))
    positions, left = {}, MARGIN
    for level in sorted(columns):
        placed, column_width = _place_column(
            columns[level], left, total_height
        )
        positions.update(placed)
        left += column_width + GAP_X
    return positions, left - GAP_X + MARGIN, total_height + 2 * MARGIN + ARC


def _edge_path(source, target):
    """Путь SVG для ребра между двумя позициями."""
    (sx, sy, sw), (tx, ty, tw) = source, target
    if tx > sx:
        start_x, end_x = sx + sw / 2, tx - tw / 2
        shift = (end_x - start_x) / 2
        return (f"M{start_x},{sy} C{start_x + shift},{sy} "
                f"{end_x - shift},{ty} {end_x},{ty}")
    top = NODE_HEIGHT / 2
    if tx == sx and ty == sy:
        return (f"M{sx - LOOP / 2},{sy - top} "
                f"C{sx - LOOP},{sy - top - SELF_ARC} "
                f"{sx + LOOP},{sy - top - SELF_ARC} {sx + LOOP / 2},{sy - top}")
    return (f"M{sx},{sy - top} C{sx},{sy - top - ARC} "
            f"{tx},{ty - top - ARC} {tx},{ty - top}")


def _edge_element(source, target, positions, is_cycle):
    """Элемент <path> для одного ребра."""
    kind = "cycle" if is_cycle else "edge"
    color = CYCLE_COLOR if is_cycle else EDGE_COLOR
    dash = ' stroke-dasharray="6 4"' if is_cycle else ""
    path = _edge_path(positions[source], positions[target])
    return (f'<path d="{path}" fill="none" stroke="{color}"{dash} '
            f'marker-end="url(#arrow-{kind})"/>')


def _node_element(name, position, is_root):
    """Элементы <rect> и <text> для одной вершины."""
    x, y, width = position
    fill = ROOT_FILL if is_root else NODE_FILL
    return (
        f'<rect x="{x - width / 2}" y="{y - NODE_HEIGHT / 2}" '
        f'width="{width}" height="{NODE_HEIGHT}" rx="6" fill="{fill}" '
        f'stroke="#333333"/>'
        f'<text x="{x}" y="{y}" text-anchor="middle" '
        f'dominant-baseline="central">{escape(name)}</text>'
    )


def render_svg(graph):
    """Формирует SVG-изображение графа зависимостей."""
    positions, width, height = layout(graph)
    cycle_edges = back_edges(graph)
    parts = [
        SVG_HEADER.format(w=width, h=height),
        ARROW.format(kind="edge", color=EDGE_COLOR),
        ARROW.format(kind="cycle", color=CYCLE_COLOR),
        f"<title>{escape('Граф зависимостей ' + graph.root)}</title>",
        '<rect width="100%" height="100%" fill="#ffffff"/>',
    ]
    for source, targets in graph.edges.items():
        for target in targets:
            is_cycle = (source, target) in cycle_edges
            parts.append(_edge_element(source, target, positions, is_cycle))
    for name, position in positions.items():
        parts.append(_node_element(name, position, name == graph.root))
    parts.append("</svg>")
    return "\n".join(parts) + "\n"
