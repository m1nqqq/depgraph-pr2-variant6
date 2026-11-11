"""Точка входа: CLI-инструмент визуализации графа зависимостей."""

import argparse
import sys

from src.apk_index import load_index
from src.config import load_config
from src.errors import DepGraphError

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
    """Выполняет работу этапа 2: выводит прямые зависимости пакета."""
    config = load_config(args.config)
    if config.test_mode:
        raise DepGraphError("тестовый режим поддерживается с этапа 3")
    index = load_index(config.repository)
    names = index.direct_dependencies(config.package, config.version)
    print(f"Прямые зависимости {config.package} {config.version}:")
    for name in names:
        print(f"  {name}")
    if not names:
        print("  (нет зависимостей)")


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
