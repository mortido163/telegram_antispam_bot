#!/bin/bash

# Скрипт для восстановления PostgreSQL из бэкапа

set -e

if [ -z "$1" ]; then
    echo "❌ Использование: $0 <путь_к_бэкапу>"
    echo "Пример: $0 ./backups/telegram_bot_backup_20250826_120000.sql.gz"
    exit 1
fi

BACKUP_FILE="$1"
DOCKER_CONTAINER="telegram_bot_postgres"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ Файл бэкапа не найден: $BACKUP_FILE"
    exit 1
fi

echo "⚠️  ВНИМАНИЕ: Это удалит все текущие данные!"
echo "📁 Файл бэкапа: $BACKUP_FILE"
read -p "Продолжить? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Отменено пользователем"
    exit 1
fi

echo "🗄️ Остановка приложения..."
docker compose stop telegram-bot

echo "🔄 Восстановление базы данных..."

# Распаковка если файл сжат
if [[ "$BACKUP_FILE" == *.gz ]]; then
    echo "📦 Распаковка бэкапа..."
    TEMP_FILE="/tmp/restore_$(date +%s).sql"
    gunzip -c "$BACKUP_FILE" > "$TEMP_FILE"
    RESTORE_FILE="$TEMP_FILE"
else
    RESTORE_FILE="$BACKUP_FILE"
fi

# Удаление и пересоздание базы данных
docker compose exec postgres psql -U postgres -c "DROP DATABASE IF EXISTS telegram_bot;"
docker compose exec postgres psql -U postgres -c "CREATE DATABASE telegram_bot;"

# Восстановление данных
docker compose exec -T postgres psql -U postgres -d telegram_bot < "$RESTORE_FILE"

# Удаление временного файла
if [[ "$BACKUP_FILE" == *.gz ]]; then
    rm -f "$TEMP_FILE"
fi

echo "🚀 Запуск приложения..."
docker compose up -d telegram-bot

echo "✅ Восстановление завершено успешно!"
