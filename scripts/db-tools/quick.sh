#!/bin/bash

# Быстрые команды для работы с БД Telegram Bot

PSQL="psql -h postgres -U postgres -d telegram_bot"

case "$1" in
    "users")
        echo "👥 Последние пользователи:"
        $PSQL -c "
        SELECT 
            user_id,
            chat_id,
            warnings_count,
            is_banned,
            last_warning_time
        FROM users 
        ORDER BY last_warning_time DESC NULLS LAST
        LIMIT 20;
        "
        ;;
    "violations")
        echo "🚫 Последние нарушения:"
        $PSQL -c "
        SELECT 
            m.timestamp,
            m.user_id,
            m.chat_id,
            left(m.text, 50) as message_preview,
            m.violation_words
        FROM messages m
        WHERE m.contains_violations = true
        ORDER BY m.timestamp DESC
        LIMIT 20;
        "
        ;;
    "stats")
        echo "📊 Общая статистика:"
        $PSQL -c "
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
    "chat")
        if [ -z "$2" ]; then
            echo "❌ Укажите chat_id: $0 chat <chat_id>"
            exit 1
        fi
        echo "💬 Статистика чата $2:"
        $PSQL -c "
        SELECT 
            'Users in chat' as metric, COUNT(DISTINCT user_id)::text as value
        FROM users WHERE chat_id = $2
        UNION ALL
        SELECT 
            'Messages in chat', COUNT(*)::text
        FROM messages WHERE chat_id = $2
        UNION ALL
        SELECT 
            'Violations in chat', COUNT(*)::text
        FROM messages WHERE chat_id = $2 AND contains_violations = true;
        "
        ;;
    "slow")
        echo "🐌 Медленные запросы:"
        $PSQL -c "
        SELECT 
            query,
            calls,
            total_time,
            mean_time
        FROM pg_stat_statements 
        WHERE calls > 10
        ORDER BY mean_time DESC 
        LIMIT 10;
        " 2>/dev/null || echo "Расширение pg_stat_statements не установлено"
        ;;
    *)
        echo "🛠️ Утилиты для работы с БД Telegram Bot"
        echo "Использование: $0 <команда>"
        echo ""
        echo "Доступные команды:"
        echo "  users       - Показать последних пользователей"
        echo "  violations  - Показать последние нарушения"
        echo "  stats       - Общая статистика"
        echo "  chat <id>   - Статистика по конкретному чату"
        echo "  slow        - Медленные запросы"
        echo ""
        echo "Примеры:"
        echo "  $0 users"
        echo "  $0 violations"
        echo "  $0 chat -1001234567890"
        ;;
esac
