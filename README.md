# depgraph - граф зависимостей пакетов Alpine Linux

Консольный инструмент визуализации графа зависимостей для менеджера
пакетов Alpine Linux (формат apk). Вариант №6, практическая работа №2
по дисциплине «Конфигурационное управление».

Готовые менеджеры пакетов и сторонние библиотеки для получения
зависимостей не используются: только стандартная библиотека Python 3.

## Состояние проекта

Реализован этап 1: чтение конфигурации из YAML и вывод параметров.

## Настройки

Все параметры задаются в YAML-файле (по умолчанию `config.yaml`).

| Параметр      | Описание                                                  |
|---------------|-----------------------------------------------------------|
| `package`     | Имя анализируемого пакета                                 |
| `repository`  | URL репозитория или путь к файлу тестового репозитория    |
| `test_mode`   | `true` - тестовый репозиторий из файла, `false` - реальный |
| `version`     | Версия пакета                                             |
| `output_file` | Имя файла с изображением графа (расширение `.svg`)       |

Поддерживается плоский YAML: строки `ключ: значение`, комментарии `#`,
значения можно брать в кавычки.

Проверки: заданы все параметры и нет лишних; в тестовом режиме имя
пакета состоит из больших латинских букв, а файл репозитория существует;
в обычном режиме `repository` - URL (`http://`, `https://`, `file://`);
версия начинается с цифры; `output_file` оканчивается на `.svg`, папка
для него существует.

## Запуск

```
run.bat [config.yaml]        (Windows)
./run.sh [config.yaml]       (Linux/macOS)
python -m src.main [config.yaml]
```

Требуется Python 3.9 или новее.

## Тесты

```
python -m unittest discover -s tests -t .
```

## Примеры

Корректная конфигурация (`config.yaml` из репозитория):

```
$ python -m src.main config.yaml
package: A
repository: examples/repo_simple.txt
test_mode: true
version: 1.0.0
output_file: graph.svg
```

Ошибки (код возврата 1):

```
$ python -m src.main none.yaml
Ошибка: файл 'none.yaml' не найден

$ python -m src.main empty.yaml
Ошибка: не заданы параметры: repository, test_mode, version, output_file

$ python -m src.main bad_package.yaml
Ошибка: package: 'abc' не подходит (большие латинские буквы)

$ python -m src.main bad_repo.yaml
Ошибка: repository: файл 'nope.txt' не найден

$ python -m src.main bad_url.yaml
Ошибка: repository: ожидается URL (http://, https:// или file://)

$ python -m src.main bad_output.yaml
Ошибка: output_file: ожидается имя файла с расширением .svg
```
