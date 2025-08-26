#!/bin/bash

# Скрипт для создания миграции базы данных

set -e

if [ -z "$1" ]; then
    echo "❌ Укажите название миграции"
    echo "Использование: $0 \"название миграции\""
    exit 1
fi

echo "🗃️ Создание миграции: $1"

# Проверяем, запущен ли PostgreSQL
if ! docker compose ps postgres | grep -q "Up"; then
    echo "🚀 Запуск PostgreSQL..."
    docker compose up -d postgres
    echo "⏳ Ожидание готовности PostgreSQL..."
    sleep 10
fi

# Создание миграции
docker compose run --rm telegram-bot alembic revision --autogenerate -m "$1"

echo "✅ Миграция создана!"
echo "📝 Проверьте созданный файл миграции в папке alembic/versions/"
echo "🚀 Для применения миграции выполните: ./scripts/migrate.sh"
