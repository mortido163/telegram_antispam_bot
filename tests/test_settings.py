"""
Тесты для модуля настроек приложения
"""
import os
from dataclasses import dataclass
from unittest.mock import patch

import pytest

from application.settings import AppConfig, AuthConfig, DatabaseConfig, LoggingConfig, ModerationConfig, PerformanceConfig


class TestAuthConfig:
    """Тесты конфигурации авторизации"""

    def test_auth_config_creation(self):
        """Тест создания конфигурации авторизации"""
        config = AuthConfig(owner_id=123456789, admin_ids=[111222333, 444555666])

        assert config.owner_id == 123456789
        assert config.admin_ids == [111222333, 444555666]

    def test_auth_config_empty_admins(self):
        """Тест создания конфигурации без администраторов"""
        config = AuthConfig(owner_id=123456789, admin_ids=[])

        assert config.owner_id == 123456789
        assert config.admin_ids == []


class TestDatabaseConfig:
    """Тесты конфигурации базы данных"""

    def test_database_config_postgresql(self):
        """Тест конфигурации PostgreSQL"""
        config = DatabaseConfig(
            url="postgresql+asyncpg://user:pass@localhost:5432/db", pool_size=20, max_overflow=30, echo=False
        )

        assert "postgresql" in config.url
        assert config.pool_size == 20
        assert config.max_overflow == 30
        assert config.echo is False

    def test_database_config_sqlite(self):
        """Тест конфигурации SQLite"""
        config = DatabaseConfig(url="sqlite+aiosqlite:///bot.db", pool_size=5, max_overflow=10, echo=True)

        assert "sqlite" in config.url
        assert config.pool_size == 5
        assert config.max_overflow == 10
        assert config.echo is True


class TestAppConfig:
    """Тесты основной конфигурации приложения"""

    def test_app_config_from_env_success(self):
        """Тест успешного создания конфигурации из переменных окружения"""
        env_vars = {
            "BOT_TOKEN": "test_token_123",
            "BOT_OWNER_ID": "123456789",
            "BOT_ADMIN_IDS": "111222333,444555666",
            "DATABASE_URL": "sqlite+aiosqlite:///test.db",
            "DB_POOL_SIZE": "10",
            "DB_MAX_OVERFLOW": "15",
            "DB_ECHO": "true",
            "LOG_LEVEL": "DEBUG",
            "LOG_FORMAT": "custom format",
            "DEFAULT_WARNINGS_LIMIT": "5",
            "ENABLE_AUTO_BAN": "false",
            "CACHE_TTL": "7200",
            "PATTERNS_CACHE_SIZE": "500",
            "ENVIRONMENT": "development",
            "DEBUG": "true",
        }

        with patch.dict(os.environ, env_vars):
            config = AppConfig.from_env()

            # Проверяем основные настройки
            assert config.bot_token == "test_token_123"
            assert config.environment == "development"
            assert config.debug is True

            # Проверяем авторизацию
            assert config.auth.owner_id == 123456789
            assert config.auth.admin_ids == [111222333, 444555666]

            # Проверяем БД
            assert config.database.url == "sqlite+aiosqlite:///test.db"
            assert config.database.pool_size == 10
            assert config.database.max_overflow == 15
            assert config.database.echo is True

            # Проверяем логирование
            assert config.logging.level == "DEBUG"
            assert config.logging.format == "custom format"

            # Проверяем модерацию
            assert config.moderation.default_warnings_limit == 5
            assert config.moderation.enable_auto_ban is False

            # Проверяем производительность
            assert config.performance.cache_ttl == 7200
            assert config.performance.patterns_cache_size == 500

    def test_app_config_missing_bot_token(self):
        """Тест ошибки при отсутствии BOT_TOKEN"""
        env_vars = {"BOT_OWNER_ID": "123456789"}

        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(ValueError, match="BOT_TOKEN environment variable is required"):
                AppConfig.from_env()

    def test_app_config_missing_owner_id(self):
        """Тест ошибки при отсутствии BOT_OWNER_ID"""
        env_vars = {"BOT_TOKEN": "test_token_123"}

        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(ValueError, match="BOT_OWNER_ID environment variable is required"):
                AppConfig.from_env()

    def test_app_config_invalid_owner_id(self):
        """Тест ошибки при неверном формате BOT_OWNER_ID"""
        env_vars = {"BOT_TOKEN": "test_token_123", "BOT_OWNER_ID": "not_a_number"}

        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(ValueError, match="BOT_OWNER_ID must be a valid integer"):
                AppConfig.from_env()

    def test_app_config_invalid_admin_ids(self):
        """Тест ошибки при неверном формате BOT_ADMIN_IDS"""
        env_vars = {
            "BOT_TOKEN": "test_token_123",
            "BOT_OWNER_ID": "123456789",
            "BOT_ADMIN_IDS": "111222333,not_a_number,444555666",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(ValueError, match="BOT_ADMIN_IDS must be comma-separated integers"):
                AppConfig.from_env()

    def test_app_config_empty_admin_ids(self):
        """Тест корректной обработки пустых BOT_ADMIN_IDS"""
        env_vars = {"BOT_TOKEN": "test_token_123", "BOT_OWNER_ID": "123456789", "BOT_ADMIN_IDS": ""}

        with patch.dict(os.environ, env_vars, clear=True):
            config = AppConfig.from_env()
            assert config.auth.admin_ids == []

    def test_app_config_admin_ids_with_spaces(self):
        """Тест корректной обработки BOT_ADMIN_IDS с пробелами"""
        env_vars = {
            "BOT_TOKEN": "test_token_123",
            "BOT_OWNER_ID": "123456789",
            "BOT_ADMIN_IDS": " 111222333 , 444555666 , 777888999 ",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            config = AppConfig.from_env()
            assert config.auth.admin_ids == [111222333, 444555666, 777888999]

    def test_app_config_default_values(self):
        """Тест значений по умолчанию"""
        env_vars = {"BOT_TOKEN": "test_token_123", "BOT_OWNER_ID": "123456789"}

        with patch.dict(os.environ, env_vars, clear=True):
            config = AppConfig.from_env()

            # Проверяем значения по умолчанию
            assert config.database.url == "sqlite+aiosqlite:///bot.db"
            assert config.database.pool_size == 20
            assert config.database.max_overflow == 30
            assert config.database.echo is False

            assert config.logging.level == "INFO"
            assert "%(asctime)s" in config.logging.format

            assert config.moderation.default_warnings_limit == 3
            assert config.moderation.enable_auto_ban is True

            assert config.performance.cache_ttl == 3600
            assert config.performance.patterns_cache_size == 1000

            assert config.environment == "development"
            assert config.debug is False

    def test_app_config_is_production(self):
        """Тест определения production среды"""
        env_vars = {"BOT_TOKEN": "test_token_123", "BOT_OWNER_ID": "123456789", "ENVIRONMENT": "production"}

        with patch.dict(os.environ, env_vars, clear=True):
            config = AppConfig.from_env()
            assert config.is_production() is True
            assert config.is_development() is False

    def test_app_config_is_development(self):
        """Тест определения development среды"""
        env_vars = {"BOT_TOKEN": "test_token_123", "BOT_OWNER_ID": "123456789", "ENVIRONMENT": "development"}

        with patch.dict(os.environ, env_vars, clear=True):
            config = AppConfig.from_env()
            assert config.is_development() is True
            assert config.is_production() is False


class TestConfigIntegration:
    """Интеграционные тесты конфигурации"""

    def test_production_config_validation(self):
        """Тест валидации production конфигурации"""
        env_vars = {
            "BOT_TOKEN": "prod_token_456",
            "BOT_OWNER_ID": "123456789",
            "BOT_ADMIN_IDS": "111222333",
            "DATABASE_URL": "postgresql+asyncpg://user:pass@localhost:5432/prod_db",
            "ENVIRONMENT": "production",
            "DEBUG": "false",
            "LOG_LEVEL": "WARNING",
            "ENABLE_AUTO_BAN": "true",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            config = AppConfig.from_env()

            # Проверяем production настройки
            assert config.is_production()
            assert not config.debug
            assert config.logging.level == "WARNING"
            assert "postgresql" in config.database.url
            assert config.moderation.enable_auto_ban

    def test_development_config_validation(self):
        """Тест валидации development конфигурации"""
        env_vars = {
            "BOT_TOKEN": "dev_token_789",
            "BOT_OWNER_ID": "123456789",
            "DATABASE_URL": "sqlite+aiosqlite:///dev.db",
            "ENVIRONMENT": "development",
            "DEBUG": "true",
            "LOG_LEVEL": "DEBUG",
            "DB_ECHO": "true",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            config = AppConfig.from_env()

            # Проверяем development настройки
            assert config.is_development()
            assert config.debug
            assert config.logging.level == "DEBUG"
            assert "sqlite" in config.database.url
            assert config.database.echo


if __name__ == "__main__":
    pytest.main([__file__])
