"""Точка входа: CLI-инструмент визуализации графа зависимостей."""

import argparse
import sys

from src.config import load_config
from src.errors import DepGraphError
from src.graph import build_graph, format_graph
from src.render import d2_path_for, save_image
from src.reverse import find_dependents, format_dependents
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
    parser.add_argument(
        "--reverse",
        action="store_true",
        help="вывести обратные зависимости пакета (кто от него зависит)",
    )
    return parser


def print_cycles(cycles):
    """Печатает найденные циклические зависимости, если они есть."""
    if cycles:
        print("Циклические зависимости:")
        for cycle in cycles:
            print("  " + " -> ".join(cycle))


def run_reverse(config, repo):
    """Режим обратных зависимостей (этап 4)."""
    result = find_dependents(repo, config.package)
    for line in format_dependents(result):
        print(line)
    print_cycles(result.cycles)


def run_graph(config, repo):
    """Основной режим: строит и выводит граф зависимостей."""
    graph = build_graph(repo, config.package)
    print(f"Граф зависимостей пакета {config.package}:")
    for line in format_graph(graph):
        print(f"  {line}")
    print_cycles(graph.cycles)
    renderer = save_image(graph, config.output_file)
    print(f"D2-описание: {d2_path_for(config.output_file)}")
    print(f"Изображение (SVG, {renderer}): {config.output_file}")


def run(args):
    """Загружает конфигурацию и выполняет выбранный режим."""
    config = load_config(args.config)
    repo = open_repository(config)
    if args.reverse:
        run_reverse(config, repo)
    else:
        run_graph(config, repo)


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
