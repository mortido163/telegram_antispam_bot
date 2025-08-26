#!/bin/bash

# Скрипт для разработки

set -e

echo "🛠️ Запуск в режиме разработки..."

# Проверка переменных окружения
if [ ! -f .env ]; then
    echo "❌ Файл .env не найден. Создайте его на основе .env.example"
    exit 1
fi

# Создание необходимых директорий
mkdir -p logs data

# Остановка текущих контейнеров
echo "🛑 Остановка текущих контейнеров..."
docker compose -f docker-compose.dev.yml down

# Сборка образов
echo "🔨 Сборка Docker образов..."
docker compose -f docker-compose.dev.yml build

# Запуск в режиме разработки
echo "🚀 Запуск в режиме разработки..."
docker compose -f docker-compose.dev.yml up -d

# Проверка статуса
echo "✅ Проверка статуса..."
docker compose -f docker-compose.dev.yml ps

echo "🎉 Запуск в режиме разработки завершен!"
echo "📖 Логи бота: docker-compose -f docker-compose.dev.yml logs -f telegram-bot"
