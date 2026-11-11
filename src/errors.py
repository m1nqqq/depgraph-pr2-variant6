"""Исключения приложения."""


class DepGraphError(Exception):
    """Базовая ошибка приложения с понятным пользователю сообщением."""


class ConfigError(DepGraphError):
    """Ошибка в конфигурационном файле."""


class RepositoryError(DepGraphError):
    """Ошибка получения или разбора данных репозитория."""


class RenderError(DepGraphError):
    """Ошибка при создании изображения графа."""
