"""Источники данных о зависимостях: тестовый и репозиторий apk."""

from src.errors import RepositoryError


class DictRepository:
    """Репозиторий в виде словаря «пакет -> список зависимостей»."""

    def __init__(self, edges):
        """Копирует словарь зависимостей."""
        self.edges = {name: list(deps) for name, deps in edges.items()}

    def dependencies(self, name):
        """Прямые зависимости пакета (у неописанного пакета их нет)."""
        return list(self.edges.get(name, ()))

    def require(self, name):
        """Проверяет, что пакет описан в репозитории."""
        if name not in self.edges:
            raise RepositoryError(
                f"пакет '{name}' не описан в тестовом репозитории"
            )


class ApkRepository:
    """Репозиторий apk: зависимости берутся из загруженного индекса."""

    def __init__(self, index, root, version):
        """Запоминает индекс и версию корневого пакета."""
        self.index = index
        self.pinned = {root: version}

    def dependencies(self, name):
        """Прямые зависимости пакета нужной версии."""
        version = self.pinned.get(name)
        if version is None:
            records = self.index.by_name.get(name)
            if not records:
                return []
            version = records[0].version
        return self.index.direct_dependencies(name, version)

    def require(self, name):
        """Проверяет, что пакет (заданной версии) есть в индексе."""
        version = self.pinned.get(name)
        records = self.index.by_name.get(name)
        if version is not None:
            self.index.find(name, version)
        elif not records:
            raise RepositoryError(f"пакет '{name}' не найден в репозитории")
