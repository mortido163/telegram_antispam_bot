import logging
from datetime import datetime
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.message import Message
from domain.entities.user import User
from domain.interfaces.repositories import MessageRepository, UserRepository
from infrastructure.database.models import MessageModel, UserModel
from infrastructure.database.session import get_session_manager

logger = logging.getLogger(__name__)


class SQLAlchemyUserRepository(UserRepository):
    async def get_by_id(self, user_id: int, chat_id: int) -> Optional[User]:
        try:
            async with get_session_manager().session() as session:
                result = await session.execute(
                    select(UserModel).where(UserModel.user_id == user_id, UserModel.chat_id == chat_id)
                )
                user_model = result.scalar_one_or_none()

                if user_model is None:
                    return None

                return User(
                    user_id=user_model.user_id,
                    chat_id=user_model.chat_id,
                    warnings_count=user_model.warnings_count,
                    is_banned=user_model.is_banned,
                    can_send_messages=user_model.can_send_messages,
                    last_warning_time=user_model.last_warning_time,
                )
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при получении пользователя {user_id} из чата {chat_id}: {e}")
            return None

    async def save(self, user: User) -> None:
        try:
            async with get_session_manager().session() as session:
                user_model = await self._get_or_create_user_model(session, user)

                user_model.warnings_count = user.warnings_count
                user_model.is_banned = user.is_banned
                user_model.can_send_messages = user.can_send_messages
                user_model.last_warning_time = user.last_warning_time

                session.add(user_model)
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при сохранении пользователя {user.user_id}: {e}")
            raise

    async def update_warnings(self, user_id: int, chat_id: int, warnings_count: int) -> None:
        try:
            async with get_session_manager().session() as session:
                result = await session.execute(
                    select(UserModel).where(UserModel.user_id == user_id, UserModel.chat_id == chat_id)
                )
                user_model = result.scalar_one_or_none()

                if user_model:
                    user_model.warnings_count = warnings_count
                    user_model.last_warning_time = datetime.utcnow()
                    session.add(user_model)
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при обновлении предупреждений для пользователя {user_id}: {e}")
            raise

    async def _get_or_create_user_model(self, session: AsyncSession, user: User) -> UserModel:
        result = await session.execute(
            select(UserModel).where(UserModel.user_id == user.user_id, UserModel.chat_id == user.chat_id)
        )
        user_model = result.scalar_one_or_none()

        if user_model is None:
            user_model = UserModel(user_id=user.user_id, chat_id=user.chat_id)

        return user_model


class SQLAlchemyMessageRepository(MessageRepository):
    async def save(self, message: Message) -> None:
        try:
            async with get_session_manager().session() as session:
                message_model = MessageModel(
                    message_id=message.message_id,
                    chat_id=message.chat_id,
                    user_id=message.user_id,
                    text=message.text,
                    timestamp=message.timestamp,
                    contains_violations=message.contains_violations,
                    violation_words=message.violation_words,
                )
                session.add(message_model)
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при сохранении сообщения {message.message_id}: {e}")
            raise

    async def get_user_violations(self, user_id: int, chat_id: int) -> List[Message]:
        try:
            async with get_session_manager().session() as session:
                result = await session.execute(
                    select(MessageModel)
                    .where(
                        MessageModel.user_id == user_id,
                        MessageModel.chat_id == chat_id,
                        MessageModel.contains_violations == True,
                    )
                    .order_by(MessageModel.timestamp.desc())
                )
                message_models = result.scalars().all()

                return [
                    Message(
                        message_id=m.message_id,
                        user_id=m.user_id,
                        chat_id=m.chat_id,
                        text=m.text,
                        timestamp=m.timestamp,
                        contains_violations=m.contains_violations,
                        violation_words=m.violation_words,
                    )
                    for m in message_models
                ]
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при получении нарушений пользователя {user_id}: {e}")
            return []

    async def get_recent_messages(self, chat_id: int, limit: int = 100) -> List[Message]:
        try:
            async with get_session_manager().session() as session:
                result = await session.execute(
                    select(MessageModel)
                    .where(MessageModel.chat_id == chat_id)
                    .order_by(MessageModel.timestamp.desc())
                    .limit(limit)
                )
                message_models = result.scalars().all()

                return [
                    Message(
                        message_id=m.message_id,
                        user_id=m.user_id,
                        chat_id=m.chat_id,
                        text=m.text,
                        timestamp=m.timestamp,
                        contains_violations=m.contains_violations,
                        violation_words=m.violation_words,
                    )
                    for m in message_models
                ]
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при получении последних сообщений для чата {chat_id}: {e}")
            return []
