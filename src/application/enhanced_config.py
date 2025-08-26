import logging
import re
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database.models import ChatConfigModel
from infrastructure.database.session import get_session_manager

logger = logging.getLogger(__name__)


class EnhancedModerationConfig:
    """
    Улучшенная конфигурация модерации с поддержкой базы данных
    и кэшированием для лучшей производительности
    """

    def __init__(self):
        self._cached_configs = {}  # Кэш конфигураций чатов
        self._compiled_patterns_cache = {}  # Кэш скомпилированных регулярных выражений
        self.default_warnings_limit = 3

    async def get_warnings_limit(self, chat_id: int) -> int:
        """Получить лимит предупреждений для конкретного чата"""
        config = await self._get_chat_config(chat_id)
        return config.warnings_limit if config else self.default_warnings_limit

    async def set_warnings_limit(self, chat_id: int, limit: int) -> None:
        """Установить лимит предупреждений для конкретного чата"""
        if limit < 1:
            raise ValueError("Лимит предупреждений должен быть положительным")

        try:
            session_manager = get_session_manager()
            async with get_session_manager().session() as session:
                config = await self._get_or_create_chat_config(session, chat_id)
                config.warnings_limit = limit
                session.add(config)

                # Обновляем кэш
                self._cached_configs[chat_id] = config
                logger.info(f"Установлен лимит предупреждений {limit} для чата {chat_id}")
        except Exception as e:
            logger.error(f"Ошибка при установке лимита предупреждений для чата {chat_id}: {e}")
            raise

    async def add_forbidden_word(self, chat_id: int, word: str) -> None:
        """Добавить запрещенное слово для конкретного чата"""
        word = word.lower().strip()
        if not word:
            return

        try:
            async with get_session_manager().session() as session:
                config = await self._get_or_create_chat_config(session, chat_id)

                # Инициализируем список если он пустой
                if config.forbidden_words is None:
                    config.forbidden_words = []

                if word not in config.forbidden_words:
                    config.forbidden_words.append(word)
                    session.add(config)

                    # Сбрасываем кэш паттернов для этого чата
                    self._invalidate_patterns_cache(chat_id)
                    self._cached_configs[chat_id] = config

                    logger.info(f"Добавлено запрещенное слово '{word}' для чата {chat_id}")
        except Exception as e:
            logger.error(f"Ошибка при добавлении запрещенного слова для чата {chat_id}: {e}")
            raise

    async def remove_forbidden_word(self, chat_id: int, word: str) -> None:
        """Удалить запрещенное слово для конкретного чата"""
        word = word.lower().strip()

        try:
            async with get_session_manager().session() as session:
                config = await self._get_chat_config_from_db(session, chat_id)

                if config and config.forbidden_words and word in config.forbidden_words:
                    config.forbidden_words.remove(word)
                    session.add(config)

                    # Сбрасываем кэш паттернов для этого чата
                    self._invalidate_patterns_cache(chat_id)
                    self._cached_configs[chat_id] = config

                    logger.info(f"Удалено запрещенное слово '{word}' для чата {chat_id}")
        except Exception as e:
            logger.error(f"Ошибка при удалении запрещенного слова для чата {chat_id}: {e}")
            raise

    async def get_forbidden_words(self, chat_id: int) -> List[str]:
        """Получить список запрещенных слов для чата"""
        config = await self._get_chat_config(chat_id)
        return config.forbidden_words if config and config.forbidden_words else []

    async def check_text(self, chat_id: int, text: str) -> List[str]:
        """Проверить текст на запрещенные слова и вернуть список найденных слов"""
        if not text:
            return []

        forbidden_words = await self.get_forbidden_words(chat_id)
        if not forbidden_words:
            return []

        text_lower = text.lower()
        found_words = []

        # Используем кэшированные паттерны для лучшей производительности
        patterns = await self._get_compiled_patterns(chat_id, forbidden_words)

        for word, pattern in zip(forbidden_words, patterns):
            if pattern.search(text_lower):
                found_words.append(word)

        return found_words

    async def clear_forbidden_words(self, chat_id: int) -> None:
        """Очистить все запрещенные слова для чата"""
        try:
            session_manager = get_session_manager()
            async with session_manager.session() as session:
                config = await self._get_or_create_chat_config(session, chat_id)
                config.forbidden_words = []
                session.add(config)

                # Сбрасываем кэш паттернов для этого чата
                self._invalidate_patterns_cache(chat_id)
                # Обновляем кэш конфигурации
                self._cached_configs[chat_id] = config
                logger.info(f"Очищены все запрещенные слова для чата {chat_id}")
        except Exception as e:
            logger.error(f"Ошибка при очистке запрещенных слов для чата {chat_id}: {e}")
            raise

    async def _get_chat_config(self, chat_id: int) -> Optional[ChatConfigModel]:
        """Получить конфигурацию чата (с кэшированием)"""
        if chat_id in self._cached_configs:
            return self._cached_configs[chat_id]

        try:
            async with get_session_manager().session() as session:
                config = await self._get_chat_config_from_db(session, chat_id)
                if config:
                    self._cached_configs[chat_id] = config
                return config
        except Exception as e:
            logger.error(f"Ошибка при получении конфигурации чата {chat_id}: {e}")
            return None

    async def _get_chat_config_from_db(self, session: AsyncSession, chat_id: int) -> Optional[ChatConfigModel]:
        """Получить конфигурацию чата из базы данных"""
        result = await session.execute(select(ChatConfigModel).where(ChatConfigModel.chat_id == chat_id))
        return result.scalar_one_or_none()

    async def _get_or_create_chat_config(self, session: AsyncSession, chat_id: int) -> ChatConfigModel:
        """Получить или создать конфигурацию чата"""
        config = await self._get_chat_config_from_db(session, chat_id)

        if config is None:
            config = ChatConfigModel(chat_id=chat_id, warnings_limit=self.default_warnings_limit, forbidden_words=[])

        return config

    async def _get_compiled_patterns(self, chat_id: int, words: List[str]) -> List[re.Pattern]:
        """Получить скомпилированные регулярные выражения для запрещенных слов"""
        cache_key = f"{chat_id}_{hash(tuple(words))}"

        if cache_key not in self._compiled_patterns_cache:
            patterns = []
            for word in words:
                # Создаем паттерн для поиска слова как отдельного слова (не часть другого слова)
                pattern = re.compile(r"\b" + re.escape(word) + r"\b", re.IGNORECASE)
                patterns.append(pattern)

            self._compiled_patterns_cache[cache_key] = patterns

        return self._compiled_patterns_cache[cache_key]

    def _invalidate_patterns_cache(self, chat_id: int) -> None:
        """Сбросить кэш скомпилированных паттернов для чата"""
        keys_to_remove = [key for key in self._compiled_patterns_cache.keys() if key.startswith(f"{chat_id}_")]
        for key in keys_to_remove:
            del self._compiled_patterns_cache[key]

    def clear_cache(self, chat_id: Optional[int] = None) -> None:
        """Очистить кэш конфигураций"""
        if chat_id:
            self._cached_configs.pop(chat_id, None)
            self._invalidate_patterns_cache(chat_id)
        else:
            self._cached_configs.clear()
            self._compiled_patterns_cache.clear()
