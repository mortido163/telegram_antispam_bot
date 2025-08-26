"""
Общие фикстуры для тестов
"""
import os
import sys
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import asyncio
import pytest
from dotenv import load_dotenv

# Добавляем src в путь для импортов
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# Загружаем тестовые переменные окружения
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env.test"))


@pytest.fixture(scope="session")
def event_loop():
    """Создание event loop для всей сессии тестов"""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_config():
    """Базовая мок-конфигурация для тестов"""
    config = Mock()

    # Database config
    config.database = Mock()
    config.database.url = "sqlite:///:memory:"
    config.database.echo = False
    config.database.pool_size = 5
    config.database.max_overflow = 10

    # Telegram config
    config.telegram = Mock()
    config.telegram.bot_token = "123456:TEST_BOT_TOKEN"
    config.telegram.webhook_url = "https://example.com/webhook"
    config.telegram.webhook_path = "/webhook"
    config.telegram.host = "0.0.0.0"
    config.telegram.port = 8080
    config.telegram.owner_id = 999888777
    config.telegram.admin_ids = [111222333, 444555666]

    # Authorization config
    config.authorization = Mock()
    config.authorization.owner_id = 999888777
    config.authorization.admin_ids = [111222333, 444555666]
    config.authorization.moderator_ids = [777888999]

    # Moderation config
    config.moderation = Mock()
    config.moderation.warnings_limit = 3
    config.moderation.auto_ban_enabled = True
    config.moderation.auto_mute_enabled = True
    config.moderation.spam_detection_enabled = True

    return config


@pytest.fixture
def mock_database_session():
    """Мок сессии базы данных"""
    session = AsyncMock()
    session.add = Mock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.refresh = AsyncMock()
    session.close = AsyncMock()
    session.execute = AsyncMock()
    session.scalar = AsyncMock()
    session.scalars = AsyncMock()
    return session


@pytest.fixture
def mock_user_repository():
    """Мок репозитория пользователей"""
    repo = AsyncMock()
    repo.get_by_id = AsyncMock()
    repo.get_by_user_and_chat = AsyncMock()
    repo.create = AsyncMock()
    repo.update = AsyncMock()
    repo.delete = AsyncMock()
    repo.get_all_in_chat = AsyncMock()
    return repo


@pytest.fixture
def mock_message_repository():
    """Мок репозитория сообщений"""
    repo = AsyncMock()
    repo.create = AsyncMock()
    repo.get_by_id = AsyncMock()
    repo.get_recent_by_user = AsyncMock()
    repo.get_by_chat = AsyncMock()
    repo.delete_old = AsyncMock()
    return repo


@pytest.fixture
def mock_moderation_service():
    """Мок сервиса модерации"""
    service = AsyncMock()
    service.check_message = AsyncMock(return_value=[])
    service.ban_user = AsyncMock()
    service.unban_user = AsyncMock()
    service.mute_user = AsyncMock()
    service.unmute_user = AsyncMock()
    service.kick_user = AsyncMock()
    service.warn_user = AsyncMock()
    service.clear_warnings = AsyncMock()
    service.set_warnings_limit = AsyncMock()
    service.get_warnings_limit = AsyncMock(return_value=3)
    service.add_forbidden_word = AsyncMock()
    service.remove_forbidden_word = AsyncMock(return_value=True)
    service.get_forbidden_words = AsyncMock(return_value=[])
    service.clear_forbidden_words = AsyncMock()
    return service


@pytest.fixture
def sample_user():
    """Создание образца пользователя для тестов"""
    from domain.entities.user import User

    return User(
        user_id=123456789, chat_id=-100123456789, warnings=0, is_banned=False, is_muted=False, created_at=datetime.now()
    )


@pytest.fixture
def sample_message():
    """Создание образца сообщения для тестов"""
    from domain.entities.message import Message

    return Message(message_id=100, user_id=123456789, chat_id=-100123456789, text="Test message", timestamp=datetime.now())


@pytest.fixture
def mock_telegram_message():
    """Мок сообщения Telegram"""
    from aiogram.types import Chat as TelegramChat
    from aiogram.types import Message as TelegramMessage
    from aiogram.types import User as TelegramUser

    message = Mock(spec=TelegramMessage)
    message.message_id = 123
    message.text = "test message"
    message.date = datetime.now()

    # Mock user
    message.from_user = Mock(spec=TelegramUser)
    message.from_user.id = 123456789
    message.from_user.username = "testuser"
    message.from_user.first_name = "Test"
    message.from_user.last_name = "User"
    message.from_user.is_bot = False

    # Mock chat
    message.chat = Mock(spec=TelegramChat)
    message.chat.id = -100123456789
    message.chat.type = "supergroup"
    message.chat.title = "Test Group"

    # Mock bot
    message.bot = Mock()
    message.bot.id = 999999999
    message.bot.ban_chat_member = AsyncMock()
    message.bot.unban_chat_member = AsyncMock()
    message.bot.restrict_chat_member = AsyncMock()
    message.bot.send_message = AsyncMock()

    # Mock methods
    message.reply = AsyncMock()
    message.answer = AsyncMock()
    message.delete = AsyncMock()
    message.forward = AsyncMock()

    return message


@pytest.fixture
def mock_telegram_bot():
    """Мок Telegram бота"""
    bot = Mock()
    bot.id = 999999999
    bot.username = "test_bot"
    bot.first_name = "Test Bot"

    # API methods
    bot.get_me = AsyncMock()
    bot.send_message = AsyncMock()
    bot.ban_chat_member = AsyncMock()
    bot.unban_chat_member = AsyncMock()
    bot.restrict_chat_member = AsyncMock()
    bot.get_chat_member = AsyncMock()
    bot.set_webhook = AsyncMock()
    bot.delete_webhook = AsyncMock()
    bot.get_webhook_info = AsyncMock()
    bot.close = AsyncMock()

    return bot


@pytest.fixture
def mock_dispatcher():
    """Мок диспетчера aiogram"""
    dp = Mock()
    dp.message_handler = Mock()
    dp.callback_query_handler = Mock()
    dp.inline_handler = Mock()
    dp.register_message_handler = Mock()
    dp.register_callback_query_handler = Mock()
    return dp


@pytest.fixture(autouse=True)
def mock_environment_variables():
    """Автоматическая настройка переменных окружения для тестов"""
    env_vars = {
        "BOT_TOKEN": "123456:TEST_BOT_TOKEN",
        "DATABASE_URL": "sqlite:///:memory:",
        "OWNER_ID": "999888777",
        "ADMIN_IDS": "111222333,444555666",
        "WEBHOOK_URL": "https://example.com/webhook",
        "WEBHOOK_PATH": "/webhook",
        "HOST": "0.0.0.0",
        "PORT": "8080",
        "WARNINGS_LIMIT": "3",
        "DEBUG": "false",
    }

    with patch.dict(os.environ, env_vars, clear=False):
        yield


@pytest.fixture
def clean_database():
    """Очистка базы данных после каждого теста"""
    yield
    # Здесь можно добавить логику очистки базы данных
    # Например, удаление всех таблиц или откат транзакций


@pytest.fixture
def isolation_database():
    """Изолированная база данных для каждого теста"""
    # Создание временной базы данных в памяти
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine("sqlite:///:memory:", echo=False)
    Session = sessionmaker(bind=engine)

    # Создание таблиц
    from infrastructure.database.models import Base

    Base.metadata.create_all(engine)

    session = Session()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


class AsyncContextManagerMock:
    """Помощник для мокирования async context managers"""

    def __init__(self, return_value=None):
        self.return_value = return_value

    async def __aenter__(self):
        return self.return_value

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


@pytest.fixture
def async_context_manager():
    """Фикстура для создания async context manager моков"""
    return AsyncContextManagerMock


# Маркеры для pytest
pytestmark = [
    pytest.mark.asyncio,
]


def pytest_configure(config):
    """Конфигурация pytest"""
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line("markers", "requires_db: marks tests that require database connection")
    config.addinivalue_line("markers", "requires_network: marks tests that require network access")


def pytest_collection_modifyitems(config, items):
    """Модификация собранных тестов"""
    for item in items:
        # Автоматически добавляем маркер unit для всех тестов, если не указано иное
        if not any(mark.name in ["integration", "slow", "requires_db", "requires_network"] for mark in item.iter_markers()):
            item.add_marker(pytest.mark.unit)


# Хуки для более подробного логирования
def pytest_runtest_setup(item):
    """Выполняется перед каждым тестом"""
    print(f"\n🚀 Запуск теста: {item.name}")


def pytest_runtest_teardown(item, nextitem):
    """Выполняется после каждого теста"""
    print(f"✅ Завершен тест: {item.name}")


@pytest.fixture
def no_network_access():
    """Фикстура для блокировки сетевого доступа в тестах"""
    import socket

    def guard(*args, **kwargs):
        raise Exception("Network access blocked in tests")

    with patch.object(socket, "socket", guard):
        yield
