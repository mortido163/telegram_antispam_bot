import logging
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.application.settings import get_config

from .models import Base

logger = logging.getLogger(__name__)


class DatabaseSessionManager:
    def __init__(self, database_config=None):
        if database_config is None:
            database_config = get_config().database

        # Параметры для создания движка
        engine_kwargs = {"echo": database_config.echo, "future": True}

        # Добавляем pool параметры только для не-SQLite баз данных
        if not database_config.url.startswith("sqlite"):
            engine_kwargs.update({"pool_size": database_config.pool_size, "max_overflow": database_config.max_overflow})

        self.engine = create_async_engine(database_config.url, **engine_kwargs)
        self.session_factory = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False, autocommit=False, autoflush=False
        )
        logger.info(f"Инициализирован движок базы данных: {database_config.url}")

    async def init_db(self):
        """Инициализировать таблицы базы данных"""
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("База данных успешно инициализирована")
        except Exception as e:
            logger.error(f"Ошибка при инициализации базы данных: {e}")
            raise

    @asynccontextmanager
    async def session(self):
        """Предоставить контекст асинхронной сессии"""
        session: AsyncSession = self.session_factory()
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Ошибка в сессии базы данных: {e}")
            raise
        finally:
            await session.close()

    async def close(self):
        """Закрыть соединения с базой данных"""
        await self.engine.dispose()
        logger.info("Соединения с базой данных закрыты")


# Ленивая инициализация глобального менеджера сессий
_session_manager = None


def get_session_manager() -> DatabaseSessionManager:
    """Получить глобальный менеджер сессий (с ленивой инициализацией)"""
    global _session_manager
    if _session_manager is None:
        _session_manager = DatabaseSessionManager()
    return _session_manager


# Обратная совместимость
def __getattr__(name):
    if name == "session_manager":
        return get_session_manager()
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
