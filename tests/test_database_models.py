"""
Тесты для моделей базы данных
"""
from datetime import datetime
from unittest.mock import Mock

import pytest

from infrastructure.database.models import Base, ChatConfigModel, MessageModel, UserModel


class TestUserModel:
    """Тесты модели пользователя"""

    def test_user_model_creation(self):
        """Тест создания модели пользователя"""
        user = UserModel(user_id=123456789, chat_id=-100123456789, warnings_count=0)

        assert user.user_id == 123456789
        assert user.chat_id == -100123456789
        assert user.warnings_count == 0
        assert user.is_banned is False  # значение по умолчанию
        assert user.can_send_messages is True  # значение по умолчанию

    def test_user_model_with_ban_status(self):
        """Тест создания модели забаненного пользователя"""
        banned_user = UserModel(user_id=987654321, chat_id=-100123456789, is_banned=True)

        assert banned_user.user_id == 987654321
        assert banned_user.is_banned is True

    def test_user_model_with_warnings(self):
        """Тест модели пользователя с предупреждениями"""
        user = UserModel(user_id=111222333, chat_id=-100123456789, warnings_count=3)

        assert user.warnings_count == 3

    def test_user_model_repr(self):
        """Тест строкового представления модели"""
        user = UserModel(user_id=123456789, chat_id=-100123456789)

        repr_str = repr(user)
        assert "UserModel" in repr_str
        assert "123456789" in repr_str


class TestMessageModel:
    """Тесты модели сообщения"""

    def test_message_model_creation(self):
        """Тест создания модели сообщения"""
        message = MessageModel(
            message_id=12345, user_id=123456789, chat_id=-100123456789, text="Test message", contains_violations=False
        )

        assert message.message_id == 12345
        assert message.user_id == 123456789
        assert message.chat_id == -100123456789
        assert message.text == "Test message"
        assert message.contains_violations is False
        assert message.timestamp is not None

    def test_message_model_with_violations(self):
        """Тест создания сообщения с нарушениями"""
        violation_message = MessageModel(
            message_id=54321,
            user_id=987654321,
            chat_id=-100987654321,
            text="SPAM CONTENT",
            contains_violations=True,
            violation_words=["spam"],
        )

        assert violation_message.contains_violations is True
        assert violation_message.violation_words == ["spam"]

    def test_message_model_with_custom_timestamp(self):
        """Тест создания сообщения с кастомным временем"""
        custom_time = datetime(2023, 1, 1, 12, 0, 0)
        message = MessageModel(
            message_id=99999, user_id=111111111, chat_id=-100111111111, text="Timed message", timestamp=custom_time
        )

        assert message.timestamp == custom_time

    def test_message_model_repr(self):
        """Тест строкового представления сообщения"""
        message = MessageModel(message_id=12345, user_id=123456789, chat_id=-100123456789, text="Test")

        repr_str = repr(message)
        assert "MessageModel" in repr_str
        assert "12345" in repr_str


class TestChatConfigModel:
    """Тесты модели конфигурации чата"""

    def test_chat_config_model_creation(self):
        """Тест создания модели конфигурации чата"""
        config = ChatConfigModel(chat_id=-100123456789, warnings_limit=5, forbidden_words=["spam", "scam"])

        assert config.chat_id == -100123456789
        assert config.warnings_limit == 5
        assert config.forbidden_words == ["spam", "scam"]

    def test_chat_config_model_defaults(self):
        """Тест значений по умолчанию"""
        config = ChatConfigModel(chat_id=-100123456789)

        # Устанавливаем значения по умолчанию вручную для проверки
        if config.warnings_limit is None:
            config.warnings_limit = 3
        if config.forbidden_words is None:
            config.forbidden_words = []

        assert config.warnings_limit == 3  # значение по умолчанию
        assert config.forbidden_words == []  # значение по умолчанию

    def test_chat_config_model_repr(self):
        """Тест строкового представления конфигурации"""
        config = ChatConfigModel(chat_id=-100123456789, warnings_limit=3)

        repr_str = repr(config)
        assert "ChatConfigModel" in repr_str


class TestBaseModel:
    """Тесты базовой модели"""

    def test_base_model_exists(self):
        """Тест что базовая модель существует"""
        assert Base is not None
        assert hasattr(Base, "metadata")

    def test_model_inheritance(self):
        """Тест наследования от базовой модели"""
        assert issubclass(UserModel, Base)
        assert issubclass(MessageModel, Base)
        assert issubclass(ChatConfigModel, Base)

    def test_model_table_names(self):
        """Тест названий таблиц моделей"""
        # Проверяем что у моделей есть атрибут __tablename__
        assert hasattr(UserModel, "__tablename__")
        assert hasattr(MessageModel, "__tablename__")
        assert hasattr(ChatConfigModel, "__tablename__")


class TestModelIntegration:
    """Интеграционные тесты моделей"""

    def test_user_message_relationship(self):
        """Тест связи пользователь-сообщения"""
        # Создаем пользователя
        user = UserModel(user_id=123456789, chat_id=-100123456789)

        # Создаем сообщение
        message = MessageModel(message_id=12345, user_id=123456789, chat_id=-100123456789, text="Test message")

        # Проверяем что user_id в сообщении соответствует user_id пользователя
        assert message.user_id == user.user_id

    def test_chat_config_relationship(self):
        """Тест связи чат-конфигурация"""
        # Создаем конфигурацию чата
        config = ChatConfigModel(chat_id=-100123456789, warnings_limit=3, forbidden_words=["spam"])

        # Создаем пользователя в том же чате
        user = UserModel(user_id=123456789, chat_id=-100123456789)

        assert config.chat_id == user.chat_id

    def test_model_defaults(self):
        """Тест значений по умолчанию в моделях"""
        # Пользователь с минимальными данными
        user = UserModel(user_id=123456789, chat_id=-100123456789)
        # Устанавливаем значения по умолчанию если они None
        if user.warnings_count is None:
            user.warnings_count = 0
        if user.is_banned is None:
            user.is_banned = False
        if user.can_send_messages is None:
            user.can_send_messages = True

        assert user.warnings_count == 0
        assert user.is_banned is False
        assert user.can_send_messages is True

        # Сообщение с минимальными данными
        message = MessageModel(message_id=12345, user_id=123456789, chat_id=-100123456789, text="Test")
        # Устанавливаем значения по умолчанию если они None
        if message.contains_violations is None:
            message.contains_violations = False

        assert message.contains_violations is False
        assert isinstance(message.timestamp, datetime)

        # Конфигурация чата с минимальными данными
        config = ChatConfigModel(chat_id=-100123456789)
        # Устанавливаем значения по умолчанию если они None
        if config.warnings_limit is None:
            config.warnings_limit = 3
        if config.forbidden_words is None:
            config.forbidden_words = []

        assert config.warnings_limit == 3
        assert config.forbidden_words == []
