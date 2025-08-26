from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from domain.entities.message import Message
from domain.entities.user import User
from infrastructure.database.models import Base, MessageModel, UserModel
from infrastructure.database.session import DatabaseSessionManager
from infrastructure.repositories import SQLAlchemyMessageRepository, SQLAlchemyUserRepository


@pytest.fixture
async def db_session():
    # Use in-memory SQLite for testing
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False, future=True)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False, autocommit=False, autoflush=False)

    async with async_session() as session:
        yield session
        # Не делаем rollback - позволяем repository управлять транзакциями

    await engine.dispose()


@pytest.fixture
def mock_session_manager(db_session):
    """Mock сессионного менеджера для использования тестовой сессии"""
    from contextlib import asynccontextmanager
    from unittest.mock import AsyncMock

    @asynccontextmanager
    async def session_context():
        try:
            yield db_session
            await db_session.commit()
        except Exception:
            await db_session.rollback()
            raise

    manager_mock = AsyncMock()
    manager_mock.session = session_context

    with patch("infrastructure.repositories.get_session_manager", return_value=manager_mock):
        yield manager_mock


@pytest.fixture
def user_repository(mock_session_manager):
    return SQLAlchemyUserRepository()


@pytest.fixture
def message_repository(mock_session_manager):
    return SQLAlchemyMessageRepository()


@pytest.fixture
def user():
    return User(
        user_id=123,
        chat_id=456,
        warnings_count=1,
        is_banned=False,
        can_send_messages=True,
        last_warning_time=datetime.utcnow(),
    )


@pytest.fixture
def message():
    return Message(
        message_id=1,
        user_id=123,
        chat_id=456,
        text="test message",
        timestamp=datetime.utcnow(),
        contains_violations=True,
        violation_words=["bad"],
    )


@pytest.mark.asyncio
async def test_user_repository_save_and_get(user_repository, user):
    # Save user
    await user_repository.save(user)

    # Get saved user
    saved_user = await user_repository.get_by_id(user.user_id, user.chat_id)

    assert saved_user is not None
    assert saved_user.user_id == user.user_id
    assert saved_user.chat_id == user.chat_id
    assert saved_user.warnings_count == user.warnings_count
    assert saved_user.is_banned == user.is_banned
    assert saved_user.can_send_messages == user.can_send_messages


@pytest.mark.asyncio
async def test_user_repository_update_warnings(user_repository, user):
    # Save user
    await user_repository.save(user)

    # Update warnings
    new_warnings = 2
    await user_repository.update_warnings(user.user_id, user.chat_id, new_warnings)

    # Get updated user
    updated_user = await user_repository.get_by_id(user.user_id, user.chat_id)
    assert updated_user.warnings_count == new_warnings


@pytest.mark.asyncio
async def test_user_repository_get_nonexistent():
    repository = SQLAlchemyUserRepository()
    user = await repository.get_by_id(999, 999)
    assert user is None


@pytest.mark.asyncio
async def test_message_repository_save(message_repository, message):
    await message_repository.save(message)

    # Get saved message through violations
    violations = await message_repository.get_user_violations(message.user_id, message.chat_id)

    assert len(violations) == 1
    saved_message = violations[0]

    assert saved_message.message_id == message.message_id
    assert saved_message.user_id == message.user_id
    assert saved_message.chat_id == message.chat_id
    assert saved_message.text == message.text
    assert saved_message.contains_violations == message.contains_violations
    assert saved_message.violation_words == message.violation_words


@pytest.mark.asyncio
async def test_message_repository_get_user_violations(message_repository, message):
    # Save message with violation
    await message_repository.save(message)

    # Save message without violation
    clean_message = Message(
        message_id=2, user_id=message.user_id, chat_id=message.chat_id, text="clean message", timestamp=datetime.utcnow()
    )
    await message_repository.save(clean_message)

    # Get violations
    violations = await message_repository.get_user_violations(message.user_id, message.chat_id)

    assert len(violations) == 1
    assert violations[0].message_id == message.message_id


@pytest.mark.asyncio
async def test_message_repository_get_recent_messages(message_repository, message):
    # Save multiple messages
    await message_repository.save(message)

    message2 = Message(
        message_id=2, user_id=message.user_id, chat_id=message.chat_id, text="another message", timestamp=datetime.utcnow()
    )
    await message_repository.save(message2)

    # Get recent messages
    messages = await message_repository.get_recent_messages(message.chat_id, limit=2)

    assert len(messages) == 2
    assert messages[0].message_id == message2.message_id  # Most recent first
    assert messages[1].message_id == message.message_id
