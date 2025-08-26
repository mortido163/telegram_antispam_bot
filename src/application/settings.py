import os
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class AuthConfig:
    """Конфигурация авторизации"""

    owner_id: int
    admin_ids: List[int]


@dataclass
class DatabaseConfig:
    """Конфигурация базы данных"""

    url: str
    pool_size: int
    max_overflow: int
    echo: bool


@dataclass
class LoggingConfig:
    """Конфигурация логирования"""

    level: str
    format: str


@dataclass
class ModerationConfig:
    """Конфигурация модерации"""

    default_warnings_limit: int
    enable_auto_ban: bool

    @classmethod
    def create_default(cls) -> "ModerationConfig":
        """Создать конфигурацию модерации по умолчанию"""
        return cls(default_warnings_limit=3, enable_auto_ban=True)


@dataclass
class PerformanceConfig:
    """Конфигурация производительности"""

    cache_ttl: int
    patterns_cache_size: int


@dataclass
class AppConfig:
    """Основная конфигурация приложения"""

    bot_token: str
    auth: AuthConfig
    database: DatabaseConfig
    logging: LoggingConfig
    moderation: ModerationConfig
    performance: PerformanceConfig
    environment: str
    debug: bool

    @classmethod
    def from_env(cls) -> "AppConfig":
        """Создать конфигурацию из переменных окружения"""
        bot_token = os.getenv("BOT_TOKEN")
        if not bot_token:
            raise ValueError("BOT_TOKEN environment variable is required")

        # Конфигурация авторизации
        owner_id_str = os.getenv("BOT_OWNER_ID")
        if not owner_id_str:
            raise ValueError("BOT_OWNER_ID environment variable is required")

        try:
            owner_id = int(owner_id_str)
        except ValueError:
            raise ValueError("BOT_OWNER_ID must be a valid integer")

        admin_ids_str = os.getenv("BOT_ADMIN_IDS", "")
        admin_ids = []
        if admin_ids_str:
            try:
                admin_ids = [int(id_str.strip()) for id_str in admin_ids_str.split(",") if id_str.strip()]
            except ValueError:
                raise ValueError("BOT_ADMIN_IDS must be comma-separated integers")

        auth = AuthConfig(owner_id=owner_id, admin_ids=admin_ids)

        database = DatabaseConfig(
            url=os.getenv("DATABASE_URL", "sqlite+aiosqlite:///bot.db"),
            pool_size=int(os.getenv("DB_POOL_SIZE", "20")),
            max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "30")),
            echo=os.getenv("DB_ECHO", "false").lower() == "true",
        )

        logging_config = LoggingConfig(
            level=os.getenv("LOG_LEVEL", "INFO"),
            format=os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
        )

        moderation = ModerationConfig(
            default_warnings_limit=int(os.getenv("DEFAULT_WARNINGS_LIMIT", "3")),
            enable_auto_ban=os.getenv("ENABLE_AUTO_BAN", "true").lower() == "true",
        )

        performance = PerformanceConfig(
            cache_ttl=int(os.getenv("CACHE_TTL", "3600")), patterns_cache_size=int(os.getenv("PATTERNS_CACHE_SIZE", "1000"))
        )

        return cls(
            bot_token=bot_token,
            auth=auth,
            database=database,
            logging=logging_config,
            moderation=moderation,
            performance=performance,
            environment=os.getenv("ENVIRONMENT", "development"),
            debug=os.getenv("DEBUG", "false").lower() == "true",
        )

    def is_production(self) -> bool:
        """Проверить, запущено ли приложение в продакшене"""
        return self.environment.lower() == "production"

    def is_development(self) -> bool:
        """Проверить, запущено ли приложение в режиме разработки"""
        return self.environment.lower() == "development"


# Ленивая инициализация глобальной конфигурации
_config = None


def get_config() -> AppConfig:
    """Получить глобальную конфигурацию (с ленивой инициализацией)"""
    global _config
    if _config is None:
        _config = AppConfig.from_env()
    return _config


# Обратная совместимость - создается только при обращении
def __getattr__(name):
    if name == "config":
        return get_config()
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
