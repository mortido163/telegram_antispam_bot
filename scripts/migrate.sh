#!/bin/bash

#!/bin/bash

# Скрипт для применения миграций базы данных

set -e

echo "� Применение миграций базы данных..."

# Проверяем, запущен ли PostgreSQL
if ! docker compose ps postgres | grep -q "Up"; then
    echo "🚀 Запуск PostgreSQL..."
    docker compose up -d postgres
    echo "⏳ Ожидание готовности PostgreSQL..."
    sleep 10
fi

# Применяем миграции
echo "📊 Применение миграций через Alembic..."
docker compose run --rm telegram-bot alembic upgrade head

echo "✅ Миграции успешно применены!"

# Показываем текущую версию
echo "📍 Текущая версия базы данных:"
docker compose run --rm telegram-bot alembic current
