"""Чтение и проверка конфигурационного файла в формате YAML."""

import os
import re
from dataclasses import dataclass

from src.errors import ConfigError

REQUIRED_KEYS = (
    "package",
    "repository",
    "test_mode",
    "version",
    "output_file",
)
QUOTES = "\"'"
KEY_VALUE_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*):(?:\s+(.*))?$")
QUOTED_RE = re.compile(r"^([\"'])(.*)\1$")
PACKAGE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+-]*$")
TEST_PACKAGE_RE = re.compile(r"^[A-Z]+$")
VERSION_RE = re.compile(r"^[0-9][0-9A-Za-z._+~-]*$")
URL_PREFIXES = ("http://", "https://", "file://")
TRUE_VALUES = ("true", "yes", "on")
FALSE_VALUES = ("false", "no", "off")
SVG_SUFFIX = ".svg"


@dataclass(frozen=True)
class Config:
    """Параметры, заданные пользователем."""

    package: str
    repository: str
    test_mode: bool
    version: str
    output_file: str

    def as_pairs(self):
        """Возвращает параметры в виде списка пар (ключ, значение)."""
        return [
            ("package", self.package),
            ("repository", self.repository),
            ("test_mode", str(self.test_mode).lower()),
            ("version", self.version),
            ("output_file", self.output_file),
        ]


def _strip_comment(line):
    """Отбрасывает комментарий ``# ...`` вне кавычек."""
    quote = ""
    for index, char in enumerate(line):
        if quote:
            quote = "" if char == quote else quote
        elif char in QUOTES:
            quote = char
        elif char == "#" and (not index or line[index - 1].isspace()):
            return line[:index]
    return line


def _unquote(value):
    """Снимает парные кавычки со значения."""
    match = QUOTED_RE.match(value)
    return match.group(2) if match else value


def _split_pair(line, number):
    """Делит строку на ключ и значение, проверяя синтаксис."""
    if line[:1].isspace():
        raise ConfigError(
            f"строка {number}: вложенные структуры не поддерживаются"
        )
    match = KEY_VALUE_RE.match(line)
    if not match:
        raise ConfigError(f"строка {number}: ожидается 'ключ: значение'")
    return match.group(1), _unquote((match.group(2) or "").strip())


def parse_yaml(text):
    """Разбирает плоский YAML: строки вида ``ключ: значение``."""
    result = {}
    for number, raw in enumerate(text.splitlines(), start=1):
        line = _strip_comment(raw).rstrip()
        if not line.strip():
            continue
        key, value = _split_pair(line, number)
        if key in result:
            raise ConfigError(f"строка {number}: ключ '{key}' повторяется")
        result[key] = value
    return result


def _read_text(path):
    """Читает конфигурационный файл, преобразуя ошибки ввода-вывода."""
    if os.path.isdir(path):
        raise ConfigError(f"'{path}' является папкой, нужен файл")
    try:
        with open(path, encoding="utf-8-sig") as file:
            return file.read()
    except FileNotFoundError:
        raise ConfigError(f"файл '{path}' не найден") from None
    except IsADirectoryError:
        raise ConfigError(f"'{path}' является папкой, нужен файл") from None
    except (OSError, UnicodeDecodeError) as error:
        raise ConfigError(f"не удалось прочитать '{path}': {error}") from None


def _check_keys(raw):
    """Проверяет, что заданы все ключи и нет лишних."""
    unknown = sorted(set(raw) - set(REQUIRED_KEYS))
    if unknown:
        raise ConfigError(f"неизвестные параметры: {', '.join(unknown)}")
    missing = [key for key in REQUIRED_KEYS if key not in raw]
    if missing:
        raise ConfigError(f"не заданы параметры: {', '.join(missing)}")


def _parse_bool(value):
    """Преобразует значение параметра test_mode в bool."""
    text = value.lower()
    if text in TRUE_VALUES:
        return True
    if text in FALSE_VALUES:
        return False
    raise ConfigError(
        f"test_mode: ожидается true или false, получено '{value}'"
    )


def _check_package(value, test_mode):
    """Проверяет имя пакета."""
    if not value:
        raise ConfigError("package: имя пакета не задано")
    pattern = TEST_PACKAGE_RE if test_mode else PACKAGE_RE
    if not pattern.match(value):
        hint = "большие латинские буквы" if test_mode else "имя пакета apk"
        raise ConfigError(f"package: '{value}' не подходит ({hint})")
    return value


def _check_repository(value, test_mode):
    """Проверяет URL репозитория или путь к файлу тестового репозитория."""
    if not value:
        raise ConfigError("repository: значение не задано")
    if test_mode and not os.path.isfile(value):
        raise ConfigError(f"repository: файл '{value}' не найден")
    if not test_mode and not value.startswith(URL_PREFIXES):
        raise ConfigError(
            "repository: ожидается URL (http://, https:// или file://)"
        )
    return value


def _check_version(value):
    """Проверяет формат версии пакета."""
    if not value:
        raise ConfigError("version: версия не задана")
    if not VERSION_RE.match(value):
        raise ConfigError(f"version: '{value}' не похоже на версию apk")
    return value


def _check_output(value):
    """Проверяет имя выходного SVG-файла."""
    if not value.lower().endswith(SVG_SUFFIX):
        raise ConfigError("output_file: ожидается имя файла с расширением .svg")
    directory = os.path.dirname(value) or "."
    if not os.path.isdir(directory):
        raise ConfigError(f"output_file: папка '{directory}' не существует")
    return value


def load_config(path):
    """Загружает и проверяет конфигурацию из YAML-файла."""
    raw = parse_yaml(_read_text(path))
    _check_keys(raw)
    test_mode = _parse_bool(raw["test_mode"])
    return Config(
        package=_check_package(raw["package"], test_mode),
        repository=_check_repository(raw["repository"], test_mode),
        test_mode=test_mode,
        version=_check_version(raw["version"]),
        output_file=_check_output(raw["output_file"]),
    )
