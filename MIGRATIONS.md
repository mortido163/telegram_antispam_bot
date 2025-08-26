# 🗄️ Руководство по миграциям базы данных

Техническое руководство по работе с миграциями Alembic в Telegram Антиспам Боте.

## 📋 Применение миграций

### Команды для пользователей
```bash
# Применить все миграции (рекомендуемый способ)
./scripts/migrate.sh

# Проверить статус миграций
docker compose run --rm telegram-bot alembic current

# Просмотр истории миграций
docker compose run --rm telegram-bot alembic history
```

### Команды для разработчиков
```bash
# Создать новую миграцию после изменения models.py
./scripts/create_migration.sh "Описание изменения"

# Проверить соответствие моделей и БД
docker compose run --rm telegram-bot alembic check

# Откат на предыдущую версию (ОСТОРОЖНО!)
docker compose run --rm telegram-bot alembic downgrade -1
```

## � Текущая схема базы данных

### Таблица `users`
Хранит информацию о пользователях и их нарушениях:
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,              -- Telegram User ID
    chat_id BIGINT NOT NULL,              -- Telegram Chat ID  
    warnings_count INTEGER DEFAULT 0,     -- Количество предупреждений
    is_banned BOOLEAN DEFAULT false,      -- Статус бана
    can_send_messages BOOLEAN DEFAULT true, -- Права на отправку сообщений
    last_warning_time TIMESTAMP,          -- Время последнего предупреждения
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(user_id, chat_id)              -- Уникальная пара пользователь-чат
);
```

### Таблица `messages`  
Журнал сообщений и нарушений:
```sql
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    message_id BIGINT NOT NULL,           -- Telegram Message ID
    chat_id BIGINT NOT NULL,              -- Telegram Chat ID
    user_id BIGINT NOT NULL,              -- Telegram User ID
    text TEXT NOT NULL,                   -- Текст сообщения
    timestamp TIMESTAMP NOT NULL,         -- Время сообщения
    contains_violations BOOLEAN DEFAULT false, -- Флаг нарушений
    violation_words JSONB,                -- Массив найденных запрещенных слов
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Таблица `chat_configs`
Конфигурация модерации для чатов:
```sql
CREATE TABLE chat_configs (
    id SERIAL PRIMARY KEY,
    chat_id BIGINT UNIQUE NOT NULL,       -- Telegram Chat ID
    warnings_limit INTEGER DEFAULT 3,     -- Лимит предупреждений
    forbidden_words JSONB DEFAULT '[]',   -- Массив запрещенных слов
    is_active BOOLEAN DEFAULT true,       -- Активность модерации
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Будущие таблицы (миграция 003)
```sql
-- Динамические администраторы
CREATE TABLE admin_settings (
    id SERIAL PRIMARY KEY,
    chat_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    role VARCHAR(50) NOT NULL,            -- 'admin', 'moderator'
    permissions JSONB,                    -- Список разрешений
    granted_by BIGINT NOT NULL,           -- Кто назначил
    granted_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,                 -- Время истечения прав
    is_active BOOLEAN DEFAULT true,
    
    UNIQUE(chat_id, user_id)
);

-- Глобальные настройки бота
CREATE TABLE bot_settings (
    id SERIAL PRIMARY KEY,
    key VARCHAR(100) UNIQUE NOT NULL,     -- Ключ настройки
    value TEXT,                           -- Значение
    value_type VARCHAR(20) DEFAULT 'string', -- Тип: string, int, bool, json
    description TEXT,                     -- Описание настройки
    is_sensitive BOOLEAN DEFAULT false,   -- Скрывать в логах
    updated_by BIGINT,                    -- Кто обновил
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

## 🔍 Оптимизация производительности

### Текущие индексы
```sql
-- Быстрый поиск пользователей
CREATE INDEX idx_users_user_chat ON users(user_id, chat_id);
CREATE INDEX idx_users_banned ON users(is_banned);
CREATE INDEX idx_users_chat_warnings ON users(chat_id, warnings_count);

-- Быстрый поиск сообщений
CREATE INDEX idx_messages_chat ON messages(chat_id);
CREATE INDEX idx_messages_violations ON messages(chat_id, contains_violations);
CREATE INDEX idx_messages_timestamp ON messages(timestamp DESC);
CREATE INDEX idx_messages_user_chat ON messages(user_id, chat_id);

-- Конфигурации чатов  
CREATE INDEX idx_chat_configs_active ON chat_configs(is_active);

-- Будущие индексы (миграция 003)
CREATE INDEX idx_admin_settings_chat_user ON admin_settings(chat_id, user_id);
CREATE INDEX idx_admin_settings_expires ON admin_settings(expires_at);
CREATE INDEX idx_bot_settings_key ON bot_settings(key);
```

### Анализ производительности
```bash
# Статистика использования индексов
./scripts/db.sh query "
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes 
ORDER BY idx_scan DESC;
"

# Самые медленные запросы
./scripts/db.sh query "
SELECT query, mean_exec_time, calls, total_exec_time
FROM pg_stat_statements 
ORDER BY mean_exec_time DESC 
LIMIT 10;
"
```

## 🔧 Разработка новых миграций

### Пример: добавление новой колонки
```python
# 1. Измените модель в src/infrastructure/database/models.py
class UserModel(Base):
    # ... существующие поля ...
    reputation_score = Column(Integer, default=0)  # Новое поле

# 2. Создайте миграцию
./scripts/create_migration.sh "Add reputation score to users"

# 3. Проверьте созданный файл alembic/versions/004_add_reputation.py
def upgrade() -> None:
    op.add_column('users', sa.Column('reputation_score', sa.Integer(), default=0))

def downgrade() -> None:
    op.drop_column('users', 'reputation_score')

# 4. Примените миграцию
./scripts/migrate.sh
```

### Пример: создание новой таблицы
```python
def upgrade() -> None:
    op.create_table(
        'user_statistics',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.BigInteger, nullable=False),
        sa.Column('chat_id', sa.BigInteger, nullable=False),
        sa.Column('messages_count', sa.Integer, default=0),
        sa.Column('violations_count', sa.Integer, default=0),
        sa.Column('last_activity', sa.DateTime),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    
    # Добавление индекса
    op.create_index(
        'idx_user_stats_user_chat',
        'user_statistics',
        ['user_id', 'chat_id'],
        unique=True
    )
```

## ⚠️ Важные правила

### Безопасность миграций
1. **Всегда делайте бэкап** перед применением в production
2. **Тестируйте на копии данных** перед production
3. **Не изменяйте уже примененные миграции** - создавайте новые
4. **Проверяйте откат миграций** - убедитесь, что downgrade работает

### Конфликты миграций
```bash
# Если два разработчика создали миграции параллельно
docker compose run --rm telegram-bot alembic merge -m "Merge parallel migrations" head1 head2

# Или создайте merge миграцию вручную
./scripts/create_migration.sh "Merge conflicting migrations"
```

### Восстановление после ошибки
```bash
# 1. Откат к последней рабочей версии
docker compose run --rm telegram-bot alembic downgrade revision_id

# 2. Восстановление из бэкапа
./scripts/restore.sh backup_before_migration.sql

# 3. Исправление миграции и повторное применение
# Отредактируйте файл миграции
./scripts/migrate.sh
```

## 📊 Мониторинг миграций

### Логирование миграций
```bash
# Все операции с БД логируются
docker compose logs telegram-bot | grep -i "alembic\|migration"

# Проверка текущего состояния
docker compose run --rm telegram-bot alembic current -v
```

### Автоматические проверки
```bash
# Добавьте в CI/CD pipeline
docker compose run --rm telegram-bot alembic check
if [ $? -ne 0 ]; then
    echo "Модели не соответствуют БД! Создайте миграцию."
    exit 1
fi
```

---

💾 **Помните**: Миграции - это история изменений вашей БД. Относитесь к ним с особой осторожностью!
