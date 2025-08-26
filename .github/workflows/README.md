# CI/CD Pipeline

Данный проект использует GitHub Actions для автоматизации тестирования, проверки качества кода и безопасн![Coverage](https://codecov.io/gh/mortido163/telegram_antispam_bot/branch/master/graph/badge.svg)сти.

## Workflows

### 1. CI Pipeline (`ci.yml`)

**Запускается при:**
- Push в ветки `main` и `develop`
- Pull Request в ветки `main` и `develop`

**Что делает:**
- ✅ Запускает тесты на Python 3.9, 3.10, 3.11
- ✅ Проверяет покрытие кода (минимум 80%)
- ✅ Проверяет синтаксис с flake8
- ✅ Проверяет типы с mypy
- ✅ Загружает отчеты в Codecov
- ✅ Сохраняет артефакты с отчетами

**Задачи (Jobs):**
1. **test** - Основное тестирование
2. **security-scan** - Сканирование безопасности (bandit, safety)
3. **build-validation** - Проверка структуры проекта
4. **notify-status** - Уведомления о результатах

### 2. Pull Request Validation (`pr-validation.yml`)

**Запускается при:**
- Открытии PR в `main`
- Обновлении кода в PR

**Что делает:**
- 🚀 Быстрая проверка тестов
- 🎨 Проверка форматирования кода (black, isort)
- 📊 Проверка регрессии покрытия
- 💬 Комментирует результаты в PR

### 3. Dependency Check (`dependency-check.yml`)

**Запускается:**
- Каждый понедельник в 9:00 UTC
- Вручную через workflow_dispatch

**Что делает:**
- 🔍 Проверяет уязвимости в зависимостях
- 📦 Находит устаревшие пакеты
- 🌳 Генерирует дерево зависимостей
- 🚨 Создает issue при обнаружении уязвимостей

## Локальная разработка

### Установка инструментов

```bash
pip install black isort flake8 mypy pytest-cov
```

### Проверка перед коммитом

```bash
# Форматирование кода
black src tests
isort src tests

# Проверка линтером
flake8 src tests

# Проверка типов
mypy src

# Запуск тестов
pytest tests/ --cov=src --cov-fail-under=80
```

### Pre-commit хуки

Рекомендуется установить pre-commit хуки:

```bash
pip install pre-commit
pre-commit install
```

## Настройки качества кода

### Конфигурация в `pyproject.toml`:
- **black** - форматирование кода (длина строки 127)
- **isort** - сортировка импортов
- **pytest** - настройки тестирования
- **coverage** - настройки покрытия

### Конфигурация в `setup.cfg`:
- **flake8** - линтер (дополнительные правила)
- **mypy** - проверка типов

## Требования к коду

### ✅ Обязательные требования:
- Покрытие тестами: **≥ 80%**
- Все тесты должны проходить
- Код отформатирован через black
- Импорты отсортированы через isort
- Нет ошибок flake8

### 🔧 Рекомендации:
- Типизация с mypy
- Документация для новых функций
- Тесты для нового функционала

## Артефакты

После каждого запуска CI сохраняются артефакты:
- **coverage-report** - HTML отчет покрытия
- **security-reports** - Отчеты безопасности
- **dependency-reports** - Отчеты зависимостей

## Статусы и бейджи

Добавьте в README проекта:

```markdown
![CI](https://github.com/mortido163/telegram_antispam_bot/workflows/CI%20Pipeline/badge.svg)
![Coverage](https://codecov.io/gh/mortido163/telegram_antispam_bot/branch/main/graph/badge.svg)
```

## Отладка CI

### Локальное воспроизведение ошибок:

```bash
# Эмуляция CI окружения
export BOT_TOKEN="test_token_for_ci"
export OWNER_ID="123456789"
export ADMIN_IDS="123456789,987654321"
export DATABASE_URL="sqlite:///test.db"
export ENVIRONMENT="test"
export DEBUG="true"

# Запуск тестов как в CI
python -m pytest tests/ \
  --cov=src \
  --cov-report=xml \
  --cov-report=html \
  --cov-report=term-missing \
  --cov-fail-under=80 \
  --verbose \
  --tb=short
```

### Пропуск медленных тестов:

```bash
pytest -m "not slow"
```

## Мониторинг

- **Codecov** - отслеживание покрытия
- **GitHub Actions** - статус билдов
- **Security alerts** - автоматические issue для уязвимостей
