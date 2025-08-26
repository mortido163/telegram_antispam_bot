-- Инициализационный скрипт PostgreSQL для Telegram бота
-- Создает оптимальные настройки и расширения

-- Создание пользователя приложения (если нужен отдельный)
-- CREATE USER telegram_user WITH PASSWORD 'your_secure_password';
-- GRANT ALL PRIVILEGES ON DATABASE telegram_bot TO telegram_user;

-- Создание расширений для дополнительной функциональности
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";  -- UUID генерация
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";  -- Статистика запросов

-- Настройка схемы по умолчанию
SET default_tablespace = '';
SET default_table_access_method = heap;

-- Логирование
SELECT 'PostgreSQL initialized for Telegram Bot' as status;
