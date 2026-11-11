"""Загрузка и разбор индекса репозитория Alpine Linux (APKINDEX)."""

import io
import re
import tarfile
import urllib.error
import urllib.request
from dataclasses import dataclass

from src.errors import RepositoryError

INDEX_NAME = "APKINDEX"
INDEX_ARCHIVE = "APKINDEX.tar.gz"
TIMEOUT_SECONDS = 60
CONSTRAINT_RE = re.compile(r"[<>=~]")
BLOCK_SEPARATOR_RE = re.compile(r"\n\s*\n")
CONFLICT_MARK = "!"


@dataclass(frozen=True)
class Package:
    """Запись об одном пакете из APKINDEX."""

    name: str
    version: str
    depends: tuple
    provides: tuple


def split_dependency(token):
    """Возвращает имя из записи вида ``name>=1.2``.

    Для конфликтов (``!name``) возвращает None: это не зависимость.
    """
    if token.startswith(CONFLICT_MARK):
        return None
    return CONSTRAINT_RE.split(token, maxsplit=1)[0]


def _parse_fields(block):
    """Разбирает блок записи в словарь «буква поля -> значение»."""
    fields = {}
    for line in block.splitlines():
        key, separator, value = line.partition(":")
        if separator:
            fields[key] = value.strip()
    return fields


def _make_package(fields, number):
    """Создаёт Package из полей записи или сообщает об ошибке."""
    if "P" not in fields or "V" not in fields:
        raise RepositoryError(f"APKINDEX: запись {number} без полей P или V")
    return Package(
        name=fields["P"],
        version=fields["V"],
        depends=tuple(fields.get("D", "").split()),
        provides=tuple(fields.get("p", "").split()),
    )


def parse_index(text):
    """Разбирает текст APKINDEX в список Package."""
    packages = []
    blocks = BLOCK_SEPARATOR_RE.split(text.strip())
    for number, block in enumerate(blocks, start=1):
        if block.strip():
            packages.append(_make_package(_parse_fields(block), number))
    return packages


def read_index_text(archive_bytes):
    """Извлекает текст APKINDEX из архива APKINDEX.tar.gz."""
    try:
        buffer = io.BytesIO(archive_bytes)
        with tarfile.open(fileobj=buffer, mode="r:gz") as tar:
            member = tar.extractfile(INDEX_NAME)
            if member is None:
                raise RepositoryError("в архиве нет файла APKINDEX")
            return member.read().decode("utf-8")
    except KeyError:
        raise RepositoryError("в архиве нет файла APKINDEX") from None
    except (tarfile.TarError, OSError, EOFError, UnicodeDecodeError) as error:
        raise RepositoryError(f"архив индекса повреждён: {error}") from None


def fetch_archive(base_url):
    """Скачивает APKINDEX.tar.gz из репозитория по базовому URL."""
    url = f"{base_url.rstrip('/')}/{INDEX_ARCHIVE}"
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT_SECONDS) as response:
            return response.read()
    except urllib.error.HTTPError as error:
        raise RepositoryError(f"{url}: HTTP {error.code}") from None
    except (urllib.error.URLError, OSError, ValueError) as error:
        raise RepositoryError(f"не удалось получить {url}: {error}") from None


class ApkIndex:
    """Индекс пакетов репозитория с разрешением зависимостей."""

    def __init__(self, packages):
        """Строит таблицы поиска по имени и по предоставляемым именам."""
        self.by_name = {}
        self.providers = {}
        for package in packages:
            self.by_name.setdefault(package.name, []).append(package)
            for provided in self._provided_names(package):
                self.providers.setdefault(provided, []).append(package.name)

    @staticmethod
    def _provided_names(package):
        """Имена, которые предоставляет пакет (включая своё)."""
        names = [split_dependency(item) for item in package.provides]
        return [package.name] + [name for name in names if name]

    def find(self, name, version):
        """Находит запись пакета заданной версии."""
        records = self.by_name.get(name)
        if not records:
            raise RepositoryError(f"пакет '{name}' не найден в репозитории")
        for record in records:
            if record.version == version:
                return record
        available = ", ".join(record.version for record in records)
        raise RepositoryError(
            f"пакет '{name}': версии '{version}' нет (доступны: {available})"
        )

    def resolve(self, dependency):
        """Сопоставляет имя зависимости имени пакета-поставщика.

        Неразрешённые имена (например, из другого репозитория)
        возвращаются без изменений.
        """
        if dependency in self.by_name:
            return dependency
        providers = self.providers.get(dependency)
        return providers[0] if providers else dependency

    def direct_dependencies(self, name, version):
        """Возвращает имена прямых зависимостей пакета без повторов."""
        package = self.find(name, version)
        resolved = []
        for token in package.depends:
            dependency = split_dependency(token)
            if dependency:
                resolved.append(self.resolve(dependency))
        unique = dict.fromkeys(resolved)
        unique.pop(package.name, None)
        return list(unique)


def load_index(base_url):
    """Загружает индекс репозитория по базовому URL."""
    text = read_index_text(fetch_archive(base_url))
    return ApkIndex(parse_index(text))
