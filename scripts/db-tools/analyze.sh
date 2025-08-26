#!/bin/bash

# Скрипт для анализа производительности PostgreSQL

echo "📊 Анализ производительности Telegram Bot БД"
echo "============================================"

# Подключение к БД
PSQL="psql -h postgres -U postgres -d telegram_bot"

echo ""
echo "🗃️ Размеры таблиц:"
$PSQL -c "
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as table_size,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) as index_size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"

echo ""
echo "📈 Статистика по таблицам:"
$PSQL -c "
SELECT 
    schemaname,
    tablename,
    n_tup_ins as inserts,
    n_tup_upd as updates,
    n_tup_del as deletes,
    n_live_tup as live_rows,
    n_dead_tup as dead_rows,
    last_vacuum,
    last_autovacuum,
    last_analyze,
    last_autoanalyze
FROM pg_stat_user_tables
ORDER BY n_live_tup DESC;
"

echo ""
echo "🐌 Медленные запросы (если включено логирование):"
$PSQL -c "
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    rows
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;
" 2>/dev/null || echo "Расширение pg_stat_statements не установлено"

echo ""
echo "🔗 Активные соединения:"
$PSQL -c "
SELECT 
    pid,
    usename,
    application_name,
    client_addr,
    state,
    query_start,
    left(query, 50) as query_preview
FROM pg_stat_activity 
WHERE state != 'idle'
ORDER BY query_start;
"

echo ""
echo "💾 Использование индексов:"
$PSQL -c "
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_tup_read,
    idx_tup_fetch,
    idx_scan
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;
"
