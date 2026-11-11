"""Исключения приложения."""


class DepGraphError(Exception):
    """Базовая ошибка приложения с понятным пользователю сообщением."""


class ConfigError(DepGraphError):
    """Ошибка в конфигурационном файле."""
