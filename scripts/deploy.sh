#!/bin/bash

# Скрипт для развертывания в продакшене

set -e

echo "🚀 Развертывание Telegram Антиспам Бота..."

# Проверка переменных окружения
if [ ! -f .env ]; then
    echo "❌ Файл .env не найден. Создайте его на основе .env.example"
    exit 1
fi

# Создание необходимых директорий
sudo mkdir -p logs data monitoring/grafana/dashboards monitoring/grafana/datasources

# Остановка текущих контейнеров
echo "🛑 Остановка текущих контейнеров..."
sudo docker compose down

# Сборка образов
echo "🔨 Сборка Docker образов..."
sudo docker compose build --no-cache

# Выполнение миграций базы данных
echo "📊 Выполнение миграций базы данных..."
sudo docker compose run --rm telegram-bot alembic upgrade head

# Запуск сервисов
echo "🚀 Запуск сервисов..."
sudo docker compose up -d

# Проверка статуса
echo "✅ Проверка статуса сервисов..."
sudo docker compose ps

echo "🎉 Развертывание завершено!"
echo "📊 Grafana доступна по адресу: http://localhost:3000"
echo "🔍 Prometheus доступен по адресу: http://localhost:9090"
echo "📖 Логи бота: docker-compose logs -f telegram-bot"
