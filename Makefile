.PHONY: help test test-cov test-fast test-slow install clean run-bot run-web

# Цвета для вывода
RED=\033[0;31m
GREEN=\033[0;32m
YELLOW=\033[1;33m
NC=\033[0m # No Color

help: ## Показать это сообщение
	@echo "$(GREEN)Доступные команды:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-15s$(NC) %s\n", $$1, $$2}'

install: ## Установить зависимости
	@echo "$(GREEN)Установка зависимостей...$(NC)"
	pip install -r requirements.txt

test: ## Запустить все тесты
	@echo "$(GREEN)Запуск всех тестов...$(NC)"
	pytest

test-cov: ## Запустить тесты с покрытием кода
	@echo "$(GREEN)Запуск тестов с покрытием...$(NC)"
	pytest --cov=src --cov=web --cov-report=html --cov-report=term
	@echo "$(GREEN)Отчет сохранен в htmlcov/index.html$(NC)"

test-fast: ## Запустить только быстрые тесты
	@echo "$(GREEN)Запуск быстрых тестов...$(NC)"
	pytest -m "not slow"

test-slow: ## Запустить только медленные тесты
	@echo "$(GREEN)Запуск медленных тестов...$(NC)"
	pytest -m "slow"

test-unit: ## Запустить юнит-тесты
	@echo "$(GREEN)Запуск юнит-тестов...$(NC)"
	pytest -m "unit"

test-api: ## Запустить API тесты
	@echo "$(GREEN)Запуск API тестов...$(NC)"
	pytest -m "api"

test-watch: ## Запустить тесты в режиме наблюдения
	@echo "$(GREEN)Режим наблюдения за тестами...$(NC)"
	pytest-watch

clean: ## Очистить временные файлы
	@echo "$(GREEN)Очистка...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete
	@echo "$(GREEN)Готово!$(NC)"

run-bot: ## Запустить Telegram бота
	@echo "$(GREEN)Запуск Telegram бота...$(NC)"
	python3 main.py

run-web: ## Запустить веб-интерфейс
	@echo "$(GREEN)Запуск веб-интерфейса...$(NC)"
	python3 run_web.py

db-create: ## Создать тестовые данные
	@echo "$(GREEN)Создание тестовых данных...$(NC)"
	python3 create_test_data.py

schedule-create: ## Создать расписание на неделю
	@echo "$(GREEN)Создание расписания...$(NC)"
	python3 create_weekly_schedule.py

lint: ## Проверить код линтером
	@echo "$(GREEN)Проверка кода...$(NC)"
	flake8 src/ web/ tests/ --max-line-length=120 --exclude=venv,__pycache__,.git || true
	pylint src/ web/ --max-line-length=120 || true

format: ## Форматировать код
	@echo "$(GREEN)Форматирование кода...$(NC)"
	black src/ web/ tests/ --line-length=120 || true
	isort src/ web/ tests/ || true

check: test lint ## Полная проверка (тесты + линтер)
	@echo "$(GREEN)Проверка завершена!$(NC)"

.DEFAULT_GOAL := help

