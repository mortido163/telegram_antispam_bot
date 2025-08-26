#!/bin/bash

# Главный скрипт для работы с БД без открытых портов

set -e

function show_help() {
    echo "🗃️ Telegram Bot Database Tools"
    echo "=============================="
    echo ""
    echo "Использование: $0 <команда>"
    echo ""
    echo "Команды:"
    echo "  connect     - Подключиться к psql интерактивно"
    echo "  query       - Выполнить SQL запрос"
    echo "  stats       - Показать общую статистику"
    echo "  analyze     - Анализ производительности"
    echo "  monitor     - Мониторинг в реальном времени"
    echo "  backup      - Создать бэкап"
    echo "  debug-on    - Включить debug режим (с портами)"
    echo "  debug-off   - Выключить debug режим"
    echo ""
    echo "Примеры:"
    echo "  $0 connect"
    echo "  $0 query \"SELECT COUNT(*) FROM users\""
    echo "  $0 stats"
}

case "$1" in
    "connect")
        echo "🔗 Подключение к PostgreSQL..."
        docker compose exec postgres psql -U postgres -d telegram_bot
        ;;
    "query")
        if [ -z "$2" ]; then
            echo "❌ Укажите SQL запрос: $0 query \"SELECT * FROM users LIMIT 5\""
            exit 1
        fi
        echo "🔍 Выполнение запроса: $2"
        docker compose exec postgres psql -U postgres -d telegram_bot -c "$2"
        ;;
    "stats")
        echo "📊 Статистика Telegram Bot:"
        docker compose exec postgres psql -U postgres -d telegram_bot -c "
        SELECT 
            'Total users' as metric, COUNT(*)::text as value FROM users
        UNION ALL
        SELECT 
            'Banned users', COUNT(*)::text FROM users WHERE is_banned = true
        UNION ALL
        SELECT 
            'Total messages', COUNT(*)::text FROM messages
        UNION ALL
        SELECT 
            'Messages with violations', COUNT(*)::text FROM messages WHERE contains_violations = true
        UNION ALL
        SELECT 
            'Active chats', COUNT(DISTINCT chat_id)::text FROM chat_configs;
        "
        ;;
    "analyze")
        if docker compose ps db-tools &>/dev/null; then
            echo "📈 Запуск анализа производительности..."
            docker compose exec db-tools ./analyze.sh
        else
            echo "❌ Debug режим не активен. Запустите: $0 debug-on"
        fi
        ;;
    "monitor")
        if docker compose ps db-tools &>/dev/null; then
            echo "📡 Запуск мониторинга в реальном времени..."
            docker compose exec db-tools ./monitor.sh
        else
            echo "❌ Debug режим не активен. Запустите: $0 debug-on"
        fi
        ;;
    "backup")
        echo "💾 Создание бэкапа..."
        ./scripts/backup.sh
        ;;
    "debug-on")
        echo "🛠️ Включение debug режима..."
        docker compose -f docker-compose.yml -f docker-compose.debug.yml up -d
        echo "✅ Debug режим включен!"
        echo "🌐 pgAdmin: http://localhost:8080 (admin@example.com / admin)"
        echo "🔗 PostgreSQL: localhost:5433"
        ;;
    "debug-off")
        echo "🔒 Выключение debug режима..."
        docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
        echo "✅ Production режим активен (без открытых портов)"
        ;;
    *)
        show_help
        ;;
esac
