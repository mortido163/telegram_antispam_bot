#!/bin/bash

# Скрипт для мониторинга Telegram Bot в реальном времени

echo "📡 Мониторинг Telegram Bot БД в реальном времени"
echo "==============================================="

PSQL="psql -h postgres -U postgres -d telegram_bot"

echo "Нажмите Ctrl+C для остановки..."
echo ""

while true; do
    clear
    echo "🕐 $(date)"
    echo "============================================"
    
    echo ""
    echo "📊 Количество записей по таблицам:"
    $PSQL -t -c "
    SELECT 
        'Users: ' || COUNT(*) 
    FROM users
    UNION ALL
    SELECT 
        'Messages: ' || COUNT(*) 
    FROM messages
    UNION ALL
    SELECT 
        'Chat configs: ' || COUNT(*) 
    FROM chat_configs;
    "
    
    echo ""
    echo "🚫 Статистика нарушений за последний час:"
    $PSQL -t -c "
    SELECT 
        'Violations: ' || COUNT(*) 
    FROM messages 
    WHERE contains_violations = true 
    AND timestamp > NOW() - INTERVAL '1 hour';
    "
    
    echo ""
    echo "👥 Активные пользователи за последний час:"
    $PSQL -t -c "
    SELECT 
        'Active users: ' || COUNT(DISTINCT user_id) 
    FROM messages 
    WHERE timestamp > NOW() - INTERVAL '1 hour';
    "
    
    echo ""
    echo "🔗 Активные соединения:"
    $PSQL -t -c "
    SELECT 
        'Connections: ' || COUNT(*) 
    FROM pg_stat_activity 
    WHERE state != 'idle';
    "
    
    echo ""
    echo "💾 Размер БД:"
    $PSQL -t -c "
    SELECT 
        'DB size: ' || pg_size_pretty(pg_database_size('telegram_bot'));
    "
    
    sleep 5
done
