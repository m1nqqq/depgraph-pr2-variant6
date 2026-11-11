"""Сохранение изображения графа: D2-описание и файл SVG."""

import os
import shutil
import subprocess

from src.d2 import to_d2
from src.errors import RenderError
from src.svg_render import render_svg

D2_COMMAND = "d2"
D2_SUFFIX = ".d2"
D2_TIMEOUT_SECONDS = 120
RENDERER_D2 = "d2"
RENDERER_BUILTIN = "встроенный"


def _write_text(path, text):
    """Записывает текстовый файл в UTF-8."""
    try:
        with open(path, "w", encoding="utf-8", newline="\n") as file:
            file.write(text)
    except OSError as error:
        raise RenderError(f"не удалось записать '{path}': {error}") from None


def _run_d2(executable, d2_path, svg_path):
    """Запускает утилиту d2; возвращает True при успехе."""
    try:
        result = subprocess.run(
            [executable, d2_path, svg_path],
            capture_output=True,
            timeout=D2_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return not result.returncode and os.path.isfile(svg_path)


def d2_path_for(svg_path):
    """Имя файла с D2-описанием рядом с SVG."""
    return os.path.splitext(svg_path)[0] + D2_SUFFIX


def save_image(graph, svg_path):
    """Сохраняет D2-описание и SVG-изображение графа.

    Если в системе установлена утилита ``d2``, SVG рисует она.
    Иначе используется встроенная отрисовка. Возвращает название
    использованного средства.
    """
    d2_path = d2_path_for(svg_path)
    _write_text(d2_path, to_d2(graph))
    executable = shutil.which(D2_COMMAND)
    if executable and _run_d2(executable, d2_path, svg_path):
        return RENDERER_D2
    _write_text(svg_path, render_svg(graph))
    return RENDERER_BUILTIN
