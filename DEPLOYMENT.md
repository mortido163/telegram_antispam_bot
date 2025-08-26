# 🚀 Руководство по развертыванию

Подробное руководство по установке, настройке и эксплуатации Telegram Антиспам Бота.

## 📋 Системные требования

### Минимальные требования
- **ОС**: Linux, macOS, Windows (с WSL2)
- **Docker**: 20.10+ 
- **Docker Compose**: 2.0+
- **RAM**: 1GB свободной памяти
- **Диск**: 2GB свободного места

### Рекомендуемые для production
- **CPU**: 2+ ядра
- **RAM**: 4GB+
- **Диск**: 10GB+ (для логов и БД)
- **Сеть**: статический IP для webhook режима

## ⚙️ Конфигурация

### Обязательные переменные
```bash
# .env файл
BOT_TOKEN=1234567890:ABCdef1234ghIkl-zyx57W2v1u123ew11    # От @BotFather
BOT_OWNER_ID=123456789                                     # Ваш Telegram ID
```

### Авторизация и безопасность
```bash
# Администраторы бота (необязательно)
BOT_ADMIN_IDS=987654321,111222333,444555666

# Режим работы
ENVIRONMENT=production                # development/production
DEBUG=false                          # true для отладки
```

### База данных
```bash
# PostgreSQL (рекомендуется для production)
DATABASE_URL=postgresql+asyncpg://postgres:secure_password@postgres:5432/telegram_bot
DB_PASSWORD=your_very_secure_password_here

# SQLite (для разработки/тестирования)
# DATABASE_URL=sqlite+aiosqlite:///bot.db

# Настройки пула соединений
DB_POOL_SIZE=20                      # Размер пула
DB_MAX_OVERFLOW=30                   # Дополнительные соединения  
DB_ECHO=false                        # SQL логирование (только для отладки)
```

### Модерация
```bash
# Настройки по умолчанию
DEFAULT_WARNINGS_LIMIT=3             # Предупреждений до бана
ENABLE_AUTO_BAN=true                 # Автобан при превышении лимита

# Производительность
CACHE_TTL=3600                       # Время жизни кэша (секунды)
PATTERNS_CACHE_SIZE=1000             # Размер кэша паттернов
MAX_WORKERS=4                        # Воркеры для обработки
```

### Логирование
```bash
LOG_LEVEL=INFO                       # DEBUG/INFO/WARNING/ERROR
LOG_FORMAT="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

## 🔧 Сценарии развертывания

### 1. Разработка (Development)
```bash
# Запуск с hot-reload и открытыми портами
./scripts/dev.sh

# Остановка
docker compose -f docker-compose.dev.yml down
```

**Доступные сервисы:**
- Bot: автоперезагрузка при изменении кода
- PostgreSQL: порт 5433 (для внешнего доступа)
- pgAdmin: http://localhost:8080 (admin@example.com / admin)
- Grafana: http://localhost:3000 (admin/admin)
- Prometheus: http://localhost:9090

### 2. Production (рекомендуемый)
```bash
# Развертывание в продакшене
./scripts/deploy.sh

# Проверка статуса
docker compose ps

# Просмотр логов
docker compose logs -f telegram-bot
```

**Особенности production режима:**
- Закрытые порты БД (безопасность)
- Оптимизированные настройки PostgreSQL
- Автоматические резервные копии
- Мониторинг и алерты

### 3. Debug режим
```bash
# Включение debug режима для БД
./scripts/db.sh debug-on

# Подключение к БД для анализа  
./scripts/db.sh connect

# Выключение debug режима
./scripts/db.sh debug-off
```

## 🗄️ Управление базой данных

### Миграции
```bash
# Применить все миграции
./scripts/migrate.sh

# Проверить текущую версию
docker compose run --rm telegram-bot alembic current

# Создать новую миграцию (для разработчиков)
./scripts/create_migration.sh "Описание изменений"
```

### Резервное копирование
```bash
# Создать резервную копию
./scripts/backup.sh

# Восстановить из резервной копии
./scripts/restore.sh backup-2024-12-26.sql

# Автоматическое резервирование (добавить в cron)
0 2 * * * /path/to/project/scripts/backup.sh
```

### Администрирование БД
```bash
# Статистика БД
./scripts/db.sh stats

# Анализ производительности
./scripts/db.sh analyze

# Мониторинг в реальном времени
./scripts/db.sh monitor

# Выполнение SQL запроса
./scripts/db.sh query "SELECT COUNT(*) FROM users WHERE is_banned = true"
```

## 📊 Мониторинг и логирование

### Системные метрики
Prometheus собирает метрики:
- `telegram_bot_messages_processed_total` - обработанные сообщения
- `telegram_bot_violations_detected_total` - обнаруженные нарушения  
- `telegram_bot_users_banned_total` - заблокированные пользователи
- `telegram_bot_response_time_seconds` - время отклика
- `telegram_bot_database_errors_total` - ошибки БД

### Дашборды Grafana
Предустановленные дашборды:
- **Overview** - общая статистика работы бота
- **Performance** - производительность и время отклика
- **Database** - состояние БД и запросы
- **Security** - события безопасности и нарушения

### Логи
```bash
# Логи бота
docker compose logs -f telegram-bot

# Логи БД
docker compose logs -f postgres

# Все логи
docker compose logs -f

# Логи с фильтром по времени
docker compose logs --since="1h" telegram-bot
```

## 🔧 Обслуживание

### Обновление
```bash
# Обновление кода
git pull origin master

# Перезапуск с новой версией
./scripts/deploy.sh

# Применение миграций (если есть)
./scripts/migrate.sh
```

### Масштабирование
```bash
# Увеличение ресурсов БД (в docker-compose.yml)
services:
  postgres:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: "1.0"
```

### Очистка
```bash
# Очистка старых образов
docker image prune -f

# Очистка логов (осторожно!)
docker compose exec telegram-bot find /app/logs -name "*.log" -mtime +7 -delete

# Полная очистка системы (ОСТОРОЖНО!)
docker system prune -a --volumes
```

## 🚨 Устранение неполадок

### Проблемы с запуском
1. **Ошибка авторизации бота**
   ```bash
   # Проверьте токен
   curl -s "https://api.telegram.org/bot${BOT_TOKEN}/getMe"
   ```

2. **Ошибки БД**
   ```bash
   # Проверьте подключение к БД
   ./scripts/db.sh connect
   # Если не работает, проверьте пароли в .env
   ```

3. **Порты заняты**
   ```bash
   # Найдите процессы на портах
   lsof -i :5433,3000,9090
   # Остановите конфликтующие сервисы
   ```

### Проблемы в работе
1. **Бот не отвечает на команды**
   - Проверьте права бота в чате (должен быть администратором)
   - Убедитесь, что BOT_OWNER_ID указан правильно
   - Проверьте логи: `docker compose logs telegram-bot`

2. **Высокое потребление памяти**
   ```bash
   # Уменьшите размер пула БД
   DB_POOL_SIZE=10
   DB_MAX_OVERFLOW=15
   ```

3. **Медленная работа**
   ```bash
   # Проанализируйте БД
   ./scripts/db.sh analyze
   # Проверьте метрики в Grafana
   ```

### Восстановление после сбоя
```bash
# 1. Остановите все сервисы
docker compose down

# 2. Восстановите БД из резервной копии
./scripts/restore.sh latest_backup.sql

# 3. Перезапустите
./scripts/deploy.sh

# 4. Проверьте целостность
./scripts/db.sh stats
```

## 🔗 Интеграции

### Webhook режим (для production)
```bash
# В .env добавьте
WEBHOOK_URL=https://yourdomain.com/webhook
WEBHOOK_SECRET=random_secret_string

# Настройте reverse proxy (nginx)
# См. примеры конфигурации в docs/nginx.conf
```

### Внешний PostgreSQL
```bash
# Для использования внешней БД
DATABASE_URL=postgresql+asyncpg://user:pass@external-db:5432/botdb

# Отключите локальный postgres в docker-compose.yml
```

### Уведомления (webhook/email)
```bash
# Настройка алертов в Grafana
# Admin → Alerting → Notification channels
```

## 📞 Поддержка

При проблемах:
1. Проверьте [SECURITY.md](SECURITY.md) для вопросов безопасности
2. Изучите логи: `docker compose logs`
3. Проверьте [Issues](https://github.com/mortido163/telegram_antispam_bot/issues)
4. Создайте новый issue с подробным описанием

---

💡 **Совет**: Всегда тестируйте изменения в development режиме перед применением в production!
