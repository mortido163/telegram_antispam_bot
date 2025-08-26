import logging
from datetime import datetime
from typing import List

from application.enhanced_config import EnhancedModerationConfig
from domain.entities.message import Message
from domain.entities.user import User
from domain.exceptions import UserAlreadyBannedError, UserAlreadyMutedError, UserNotBannedError, UserNotMutedError
from domain.interfaces.moderation_service import ModerationService
from domain.interfaces.repositories import MessageRepository, UserRepository
from infrastructure.monitoring import database_time_it, metrics, time_it

logger = logging.getLogger(__name__)


class TelegramModerationService(ModerationService):
    def __init__(
        self, user_repository: UserRepository, message_repository: MessageRepository, config: EnhancedModerationConfig
    ):
        self.user_repository = user_repository
        self.message_repository = message_repository
        self.config = config

    @time_it
    async def check_message(self, message: Message) -> List[str]:
        """Проверить сообщение на нарушения и вернуть список найденных запрещенных слов"""
        metrics.increment_messages_processed(message.chat_id)

        violation_words = await self.config.check_text(message.chat_id, message.text)
        if violation_words:
            metrics.increment_violations_detected(message.chat_id)
            logger.info(f"Обнаружены нарушения в сообщении {message.message_id}: {violation_words}")
            message.contains_violations = True
            message.violation_words = violation_words
            await self.message_repository.save(message)

            user = await self.user_repository.get_by_id(message.user_id, message.chat_id)
            if user is None:
                user = User(message.user_id, message.chat_id)

            await self.warn_user(user, violation_words)

        return violation_words

    @database_time_it
    async def warn_user(self, user: User, violation_words: List[str]) -> None:
        """Выдать предупреждение пользователю и забанить, если превышен лимит предупреждений"""
        user.warnings_count += 1
        user.last_warning_time = datetime.utcnow()

        metrics.increment_warnings_issued(user.chat_id)

        logger.info(
            f"Предупреждение пользователю {user.user_id} в чате {user.chat_id}. "
            f"Текущее количество предупреждений: {user.warnings_count}"
        )

        warnings_limit = await self.get_warnings_limit(user.chat_id)
        if user.warnings_count >= warnings_limit:
            logger.warning(
                f"Пользователь {user.user_id} превысил лимит предупреждений ({warnings_limit}). " f"Автоматический бан."
            )
            await self.ban_user(user)

        await self.user_repository.save(user)

    @database_time_it
    async def ban_user(self, user: User) -> None:
        """Забанить пользователя в чате"""
        if user.is_banned:
            raise UserAlreadyBannedError(f"Пользователь {user.user_id} уже забанен в чате {user.chat_id}")

        metrics.increment_users_banned(user.chat_id)
        logger.info(f"Бан пользователя {user.user_id} в чате {user.chat_id}")
        user.is_banned = True
        user.can_send_messages = False
        await self.user_repository.save(user)

    @database_time_it
    async def unban_user(self, user: User) -> None:
        """Снять бан с пользователя"""
        if not user.is_banned:
            raise UserNotBannedError(f"Пользователь {user.user_id} не забанен в чате {user.chat_id}")

        metrics.increment_users_unbanned(user.chat_id)
        logger.info(f"Снятие бана с пользователя {user.user_id} в чате {user.chat_id}")
        user.is_banned = False
        user.can_send_messages = True
        user.warnings_count = 0  # Сброс предупреждений при разбане
        await self.user_repository.save(user)

    @database_time_it
    async def mute_user(self, user: User) -> None:
        """Ограничить пользователя в отправке сообщений"""
        if not user.can_send_messages:
            raise UserAlreadyMutedError(f"Пользователь {user.user_id} уже заглушен в чате {user.chat_id}")

        metrics.increment_users_muted(user.chat_id)
        logger.info(f"Заглушение пользователя {user.user_id} в чате {user.chat_id}")
        user.can_send_messages = False
        await self.user_repository.save(user)

    @database_time_it
    async def unmute_user(self, user: User) -> None:
        """Разрешить пользователю отправлять сообщения"""
        if user.can_send_messages:
            raise UserNotMutedError(f"Пользователь {user.user_id} не заглушен в чате {user.chat_id}")

        logger.info(f"Снятие заглушения с пользователя {user.user_id} в чате {user.chat_id}")
        user.can_send_messages = True
        await self.user_repository.save(user)

    @database_time_it
    async def kick_user(self, user: User) -> None:
        """Удалить пользователя из чата"""
        # Этот метод будет вызван обработчиком telegram бота
        # Здесь нужно только сбросить состояние пользователя
        metrics.increment_users_kicked(user.chat_id)
        logger.info(f"Кик пользователя {user.user_id} из чата {user.chat_id}")
        user.warnings_count = 0
        user.is_banned = False
        user.can_send_messages = True
        await self.user_repository.save(user)

    async def get_warnings_limit(self, chat_id: int) -> int:
        """Получить количество предупреждений до бана для конкретного чата"""
        return await self.config.get_warnings_limit(chat_id)

    async def set_warnings_limit(self, chat_id: int, limit: int) -> None:
        """Установить количество предупреждений до бана для конкретного чата"""
        logger.info(f"Установка лимита предупреждений {limit} для чата {chat_id}")
        await self.config.set_warnings_limit(chat_id, limit)

    async def add_forbidden_word(self, word: str) -> None:
        """Добавить запрещенное слово"""
        logger.info(f"Добавление запрещенного слова: {word}")
        await self.config.add_forbidden_word(word)

    async def remove_forbidden_word(self, word: str) -> bool:
        """Удалить запрещенное слово. Возвращает True если слово было удалено"""
        logger.info(f"Удаление запрещенного слова: {word}")
        return await self.config.remove_forbidden_word(word)

    async def get_forbidden_words(self) -> List[str]:
        """Получить список всех запрещенных слов"""
        return await self.config.get_forbidden_words()

    async def clear_forbidden_words(self) -> None:
        """Очистить весь список запрещенных слов"""
        logger.warning("Очистка всех запрещенных слов")
        await self.config.clear_forbidden_words()
