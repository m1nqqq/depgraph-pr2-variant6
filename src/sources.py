"""Выбор источника данных по настройкам пользователя."""

from src.apk_index import load_index
from src.file_repo import load_test_repository
from src.repo import ApkRepository


def open_repository(config):
    """Открывает тестовый или реальный репозиторий по конфигурации."""
    if config.test_mode:
        repo = load_test_repository(config.repository)
    else:
        index = load_index(config.repository)
        repo = ApkRepository(index, config.package, config.version)
    repo.require(config.package)
    return repo
