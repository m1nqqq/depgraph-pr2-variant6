"""Точка входа: CLI-инструмент визуализации графа зависимостей."""

import argparse
import sys

from src.config import load_config
from src.errors import DepGraphError
from src.graph import build_graph, format_cycles, format_graph
from src.sources import open_repository

DEFAULT_CONFIG = "config.yaml"
EXIT_OK = 0
EXIT_ERROR = 1


def build_parser():
    """Создаёт разборщик аргументов командной строки."""
    parser = argparse.ArgumentParser(
        prog="depgraph",
        description="Визуализация графа зависимостей пакетов Alpine Linux.",
    )
    parser.add_argument(
        "config",
        nargs="?",
        default=DEFAULT_CONFIG,
        help=f"путь к YAML-конфигурации (по умолчанию {DEFAULT_CONFIG})",
    )
    return parser


def run(args):
    """Выполняет работу этапа 3: строит и выводит граф зависимостей."""
    config = load_config(args.config)
    repo = open_repository(config)
    graph = build_graph(repo, config.package)
    print(f"Граф зависимостей пакета {config.package}:")
    for line in format_graph(graph):
        print(f"  {line}")
    if graph.cycles:
        print("Циклические зависимости:")
        for line in format_cycles(graph):
            print(line)


def main(argv=None):
    """Запускает приложение и возвращает код завершения."""
    args = build_parser().parse_args(argv)
    try:
        run(args)
    except DepGraphError as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return EXIT_ERROR
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
