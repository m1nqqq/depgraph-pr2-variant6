"""Тестовый репозиторий: граф зависимостей из текстового файла."""

import re

from src.errors import RepositoryError
from src.repo import DictRepository

LINE_RE = re.compile(r"^([A-Z]+)\s*:\s*(.*)$")
NAME_RE = re.compile(r"^[A-Z]+$")
COMMENT_MARK = "#"


def _parse_line(line, number):
    """Разбирает строку ``X: A B`` в пару (имя, список зависимостей)."""
    match = LINE_RE.match(line)
    if not match:
        raise RepositoryError(
            f"строка {number}: ожидается 'X: A B' (большие латинские буквы)"
        )
    dependencies = match.group(2).split()
    for name in dependencies:
        if not NAME_RE.match(name):
            raise RepositoryError(
                f"строка {number}: недопустимое имя '{name}'"
            )
    return match.group(1), list(dict.fromkeys(dependencies))


def parse_test_repository(text):
    """Разбирает текст описания тестового репозитория."""
    edges = {}
    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw.split(COMMENT_MARK, maxsplit=1)[0].strip()
        if not line:
            continue
        name, dependencies = _parse_line(line, number)
        if name in edges:
            raise RepositoryError(
                f"строка {number}: пакет '{name}' описан дважды"
            )
        edges[name] = dependencies
    return DictRepository(edges)


def load_test_repository(path):
    """Читает файл тестового репозитория."""
    try:
        with open(path, encoding="utf-8-sig") as file:
            return parse_test_repository(file.read())
    except (OSError, UnicodeDecodeError) as error:
        raise RepositoryError(
            f"не удалось прочитать '{path}': {error}"
        ) from None
