.PHONY: help test test-unit test-integration test-cov test-html test-xml install install-dev clean lint format type-check security

# Цвета для вывода
RED=\033[0;31m
GREEN=\033[0;32m
YELLOW=\033[1;33m
BLUE=\033[0;34m
NC=\033[0m # No Color

help: ## Показать справку
	@echo "$(BLUE)Доступные команды:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

install: ## Установить основные зависимости
	@echo "$(YELLOW)Установка основных зависимостей...$(NC)"
	pip install -r requirements.txt
	@echo "$(GREEN)✅ Основные зависимости установлены$(NC)"

install-dev: ## Установить зависимости для разработки
	@echo "$(YELLOW)Установка зависимостей для разработки...$(NC)"
	pip install -r requirements-dev.txt
	@echo "$(GREEN)✅ Зависимости для разработки установлены$(NC)"

test: ## Запустить все тесты
	@echo "$(YELLOW)Запуск всех тестов...$(NC)"
	pytest -v
	@echo "$(GREEN)✅ Все тесты выполнены$(NC)"

test-unit: ## Запустить только unit тесты
	@echo "$(YELLOW)Запуск unit тестов...$(NC)"
	pytest -v -m "unit"
	@echo "$(GREEN)✅ Unit тесты выполнены$(NC)"

test-integration: ## Запустить только интеграционные тесты
	@echo "$(YELLOW)Запуск интеграционных тестов...$(NC)"
	pytest -v -m "integration"
	@echo "$(GREEN)✅ Интеграционные тесты выполнены$(NC)"

test-fast: ## Запустить быстрые тесты (исключить медленные)
	@echo "$(YELLOW)Запуск быстрых тестов...$(NC)"
	pytest -v -m "not slow"
	@echo "$(GREEN)✅ Быстрые тесты выполнены$(NC)"

test-cov: ## Запустить тесты с покрытием
	@echo "$(YELLOW)Запуск тестов с анализом покрытия...$(NC)"
	pytest --cov=src --cov-report=term-missing
	@echo "$(GREEN)✅ Тесты с покрытием выполнены$(NC)"

test-html: ## Создать HTML отчет о покрытии
	@echo "$(YELLOW)Создание HTML отчета о покрытии...$(NC)"
	pytest --cov=src --cov-report=html:htmlcov
	@echo "$(GREEN)✅ HTML отчет создан в папке htmlcov/$(NC)"
	@echo "$(BLUE)Откройте htmlcov/index.html в браузере$(NC)"

test-xml: ## Создать XML отчет о покрытии
	@echo "$(YELLOW)Создание XML отчета о покрытии...$(NC)"
	pytest --cov=src --cov-report=xml
	@echo "$(GREEN)✅ XML отчет создан: coverage.xml$(NC)"

test-parallel: ## Запустить тесты параллельно
	@echo "$(YELLOW)Запуск тестов параллельно...$(NC)"
	pytest -n auto
	@echo "$(GREEN)✅ Параллельные тесты выполнены$(NC)"

test-watch: ## Запустить тесты в режиме наблюдения
	@echo "$(YELLOW)Запуск тестов в режиме наблюдения...$(NC)"
	@echo "$(BLUE)Нажмите Ctrl+C для остановки$(NC)"
	while true; do \
		pytest -v || true; \
		echo "$(YELLOW)Ожидание изменений... (Ctrl+C для выхода)$(NC)"; \
		sleep 2; \
	done

test-specific: ## Запустить конкретный тест (использование: make test-specific TEST=test_file.py::test_function)
	@echo "$(YELLOW)Запуск конкретного теста: $(TEST)$(NC)"
	pytest -v $(TEST)
	@echo "$(GREEN)✅ Тест выполнен$(NC)"

lint: ## Проверить код линтерами
	@echo "$(YELLOW)Проверка кода линтерами...$(NC)"
	flake8 src/ tests/
	@echo "$(GREEN)✅ Проверка линтерами завершена$(NC)"

format: ## Отформатировать код
	@echo "$(YELLOW)Форматирование кода...$(NC)"
	black src/ tests/
	isort src/ tests/
	@echo "$(GREEN)✅ Код отформатирован$(NC)"

type-check: ## Проверить типы
	@echo "$(YELLOW)Проверка типов...$(NC)"
	mypy src/
	@echo "$(GREEN)✅ Проверка типов завершена$(NC)"

security: ## Проверить безопасность
	@echo "$(YELLOW)Проверка безопасности...$(NC)"
	bandit -r src/
	safety check
	@echo "$(GREEN)✅ Проверка безопасности завершена$(NC)"

clean: ## Очистить временные файлы
	@echo "$(YELLOW)Очистка временных файлов...$(NC)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf coverage.xml
	rm -rf .mypy_cache/
	rm -rf dist/
	rm -rf build/
	@echo "$(GREEN)✅ Временные файлы очищены$(NC)"

check-all: lint type-check security test-cov ## Выполнить все проверки
	@echo "$(GREEN)✅ Все проверки выполнены успешно$(NC)"

setup-dev: install-dev ## Настроить среду разработки
	@echo "$(YELLOW)Настройка среды разработки...$(NC)"
	pre-commit install
	@echo "$(GREEN)✅ Среда разработки настроена$(NC)"

# Команды для CI/CD
ci-test: ## Тесты для CI/CD
	@echo "$(YELLOW)Запуск тестов для CI/CD...$(NC)"
	pytest --cov=src --cov-report=xml --cov-report=term-missing --junitxml=junit.xml

ci-check: ## Полная проверка для CI/CD
	@echo "$(YELLOW)Полная проверка для CI/CD...$(NC)"
	flake8 src/ tests/
	mypy src/
	bandit -r src/
	pytest --cov=src --cov-report=xml --cov-report=term-missing --junitxml=junit.xml
	@echo "$(GREEN)✅ Проверка CI/CD завершена$(NC)"

# Дебаг команды
test-debug: ## Запустить тесты с отладочной информацией
	@echo "$(YELLOW)Запуск тестов с отладкой...$(NC)"
	pytest -v -s --tb=long

test-pdb: ## Запустить тесты с входом в pdb при ошибке
	@echo "$(YELLOW)Запуск тестов с pdb...$(NC)"
	pytest -v --pdb

# Информационные команды
test-info: ## Показать информацию о тестах
	@echo "$(BLUE)Информация о тестах:$(NC)"
	@echo "$(YELLOW)Всего тестов:$(NC)"
	@find tests/ -name "test_*.py" -exec pytest --collect-only {} + | grep "test session starts" -A 1000 | grep "collected" | tail -1
	@echo "$(YELLOW)Структура тестов:$(NC)"
	@find tests/ -name "test_*.py" | sort

coverage-report: ## Показать детальный отчет о покрытии
	@echo "$(YELLOW)Детальный отчет о покрытии:$(NC)"
	coverage report --show-missing

# Команда по умолчанию
.DEFAULT_GOAL := help
