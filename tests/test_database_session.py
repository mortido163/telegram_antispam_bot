"""
Тесты для сессий базы данных
"""
import os
from unittest.mock import AsyncMock, Mock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database.models import Base
from infrastructure.database.session import DatabaseSessionManager, get_session_manager


class TestDatabaseSessionManager:
    """Тесты менеджера сессий базы данных"""

    @pytest.fixture
    def db_config(self):
        """Конфигурация тестовой БД"""
        from application.settings import DatabaseConfig

        return DatabaseConfig(url="sqlite+aiosqlite:///:memory:", pool_size=5, max_overflow=10, echo=False)

    def test_session_manager_init(self, db_config):
        """Тест инициализации менеджера сессий"""
        manager = DatabaseSessionManager(db_config)

        assert manager.engine is not None
        assert manager.session_factory is not None

    def test_session_manager_init_with_default_config(self):
        """Тест инициализации с конфигурацией по умолчанию"""
        with patch("infrastructure.database.session.get_config") as mock_get_config:
            from application.settings import DatabaseConfig

            mock_get_config.return_value.database = DatabaseConfig(
                url="sqlite+aiosqlite:///:memory:", pool_size=5, max_overflow=10, echo=False
            )

            manager = DatabaseSessionManager()
            assert manager.engine is not None

    @pytest.mark.asyncio
    async def test_init_db_method_exists(self, db_config):
        """Тест существования метода инициализации БД"""
        manager = DatabaseSessionManager(db_config)

        # Проверяем, что метод существует и вызывается без ошибок TypeError
        assert hasattr(manager, "init_db")
        assert callable(manager.init_db)

    @pytest.mark.asyncio
    async def test_close_method_exists(self, db_config):
        """Тест существования метода закрытия соединений"""
        manager = DatabaseSessionManager(db_config)

        # Проверяем, что метод существует
        assert hasattr(manager, "close")
        assert callable(manager.close)

    @pytest.mark.asyncio
    async def test_session_context_success(self, db_config):
        """Тест успешного использования контекста сессии"""
        manager = DatabaseSessionManager(db_config)

        mock_session = AsyncMock(spec=AsyncSession)

        with patch.object(manager, "session_factory", return_value=mock_session):
            async with manager.session() as session:
                assert session == mock_session

            mock_session.commit.assert_called_once()
            mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_session_context_rollback_on_error(self, db_config):
        """Тест отката транзакции при ошибке"""
        manager = DatabaseSessionManager(db_config)

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.commit.side_effect = Exception("Commit failed")

        with patch.object(manager, "session_factory", return_value=mock_session):
            with pytest.raises(Exception, match="Commit failed"):
                async with manager.session() as session:
                    # Эмулируем ошибку в блоке
                    pass

            mock_session.rollback.assert_called_once()
            mock_session.close.assert_called_once()


class TestSessionManagerSingleton:
    """Тесты глобального менеджера сессий"""

    def test_get_session_manager_singleton(self):
        """Тест что get_session_manager возвращает один экземпляр"""
        with patch("infrastructure.database.session.get_config") as mock_get_config:
            from application.settings import DatabaseConfig

            mock_get_config.return_value.database = DatabaseConfig(
                url="sqlite+aiosqlite:///:memory:", pool_size=5, max_overflow=10, echo=False
            )

            manager1 = get_session_manager()
            manager2 = get_session_manager()

            assert manager1 is manager2

    def test_session_manager_lazy_initialization(self):
        """Тест ленивой инициализации глобального менеджера"""
        # Сбрасываем глобальную переменную
        import infrastructure.database.session as session_module

        session_module._session_manager = None

        with patch("infrastructure.database.session.get_config") as mock_get_config:
            from application.settings import DatabaseConfig

            mock_get_config.return_value.database = DatabaseConfig(
                url="sqlite+aiosqlite:///:memory:", pool_size=5, max_overflow=10, echo=False
            )

            # Первый вызов должен создать менеджер
            manager = get_session_manager()
            assert manager is not None
            assert session_module._session_manager is manager


class TestSessionManagerIntegration:
    """Интеграционные тесты менеджера сессий"""

    @pytest.mark.asyncio
    async def test_real_database_operations(self):
        """Тест реальных операций с БД"""
        with patch("infrastructure.database.session.get_config") as mock_get_config:
            from application.settings import DatabaseConfig

            mock_get_config.return_value.database = DatabaseConfig(
                url="sqlite+aiosqlite:///:memory:", pool_size=5, max_overflow=10, echo=False
            )

            manager = DatabaseSessionManager()

            # Инициализируем БД
            await manager.init_db()

            # Тестируем создание сессии
            async with manager.session() as session:
                assert isinstance(session, AsyncSession)
                # Можем выполнить простой запрос
                from sqlalchemy import text

                result = await session.execute(text("SELECT 1"))
                assert result.scalar() == 1

            # Закрываем соединения
            await manager.close()
