#!/bin/bash

# Скрипт для создания бэкапов PostgreSQL

set -e

BACKUP_DIR="./backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="telegram_bot_backup_${TIMESTAMP}.sql"
DOCKER_CONTAINER="telegram_bot_postgres"

# Создание директории для бэкапов
mkdir -p "$BACKUP_DIR"

echo "🗄️ Создание бэкапа базы данных..."
echo "📁 Файл: $BACKUP_FILE"

# Создание бэкапа
docker compose exec postgres pg_dump \
    -U postgres \
    -d telegram_bot \
    --verbose \
    --no-owner \
    --no-privileges \
    > "$BACKUP_DIR/$BACKUP_FILE"

# Сжатие бэкапа
echo "🗜️ Сжатие бэкапа..."
gzip "$BACKUP_DIR/$BACKUP_FILE"

echo "✅ Бэкап создан: $BACKUP_DIR/${BACKUP_FILE}.gz"

# Очистка старых бэкапов (старше 7 дней)
echo "🧹 Очистка старых бэкапов..."
find "$BACKUP_DIR" -name "telegram_bot_backup_*.sql.gz" -mtime +7 -delete

echo "🎉 Бэкап завершен успешно!"
