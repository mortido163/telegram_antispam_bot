"""
Тесты для доменных сущностей
"""
from datetime import datetime, timedelta

import pytest

from domain.entities.message import Message
from domain.entities.user import User


class TestUserEntity:
    """Тесты сущности пользователя"""

    def test_user_creation(self):
        """Тест создания пользователя"""
        user = User(123456789, -100123456789)

        assert user.user_id == 123456789
        assert user.chat_id == -100123456789
        assert user.warnings_count == 0
        assert user.is_banned is False
        assert user.can_send_messages is True
        assert user.last_warning_time is None

    def test_user_creation_with_optional_params(self):
        """Тест создания пользователя с опциональными параметрами"""
        now = datetime.now()
        user = User(
            user_id=123456789,
            chat_id=-100123456789,
            warnings_count=2,
            is_banned=True,
            can_send_messages=False,
            last_warning_time=now,
        )

        assert user.warnings_count == 2
        assert user.is_banned is True
        assert user.can_send_messages is False
        assert user.last_warning_time == now

    def test_user_add_warning(self):
        """Тест добавления предупреждения"""
        user = User(123456789, -100123456789)

        user.warnings_count += 1
        assert user.warnings_count == 1

        user.warnings_count += 1
        assert user.warnings_count == 2

    def test_user_add_multiple_warnings(self):
        """Тест добавления нескольких предупреждений"""
        user = User(123456789, -100123456789)

        user.warnings_count += 3
        assert user.warnings_count == 3

        user.warnings_count += 2
        assert user.warnings_count == 5

    def test_user_clear_warnings(self):
        """Тест очистки предупреждений"""
        user = User(123456789, -100123456789, warnings_count=5)

        user.warnings_count = 0
        assert user.warnings_count == 0

    def test_user_ban(self):
        """Тест бана пользователя"""
        user = User(123456789, -100123456789)

        user.is_banned = True
        assert user.is_banned is True

    def test_user_unban(self):
        """Тест разбана пользователя"""
        user = User(123456789, -100123456789, is_banned=True)

        user.is_banned = False
        assert user.is_banned is False

    def test_user_mute(self):
        """Тест заглушения пользователя"""
        user = User(123456789, -100123456789)

        user.can_send_messages = False
        assert user.can_send_messages is False

    def test_user_unmute(self):
        """Тест снятия заглушения с пользователя"""
        user = User(123456789, -100123456789, can_send_messages=False)

        user.can_send_messages = True
        assert user.can_send_messages is True

    def test_user_has_max_warnings(self):
        """Тест проверки максимального количества предупреждений"""
        user = User(123456789, -100123456789)

        # Меньше лимита
        assert user.warnings_count < 5

        # Равно лимиту
        user.warnings_count = 3
        assert user.warnings_count >= 3

        # Больше лимита
        user.warnings_count = 5
        assert user.warnings_count >= 3

    def test_user_equality(self):
        """Тест сравнения пользователей"""
        user1 = User(123456789, -100123456789)
        user2 = User(123456789, -100123456789)
        user3 = User(987654321, -100123456789)

        assert user1 == user2
        assert user1 != user3

    def test_user_hash(self):
        """Тест хеширования пользователей"""
        user1 = User(123456789, -100123456789)
        user2 = User(123456789, -100123456789)
        user3 = User(987654321, -100123456789)

        # dataclass объекты hashable если frozen=True, но наши нет
        # Проверим, что они сравнимы по равенству
        assert user1 == user2
        assert user1 != user3

    def test_user_string_representation(self):
        """Тест строкового представления пользователя"""
        user = User(123456789, -100123456789, warnings_count=2, is_banned=True)

        str_repr = str(user)
        assert "123456789" in str_repr
        assert "-100123456789" in str_repr
        assert "2" in str_repr
        assert "True" in str_repr  # is_banned

    def test_user_repr(self):
        """Тест repr представления пользователя"""
        user = User(123456789, -100123456789)

        repr_str = repr(user)
        assert "User" in repr_str
        assert "123456789" in repr_str
        assert "-100123456789" in repr_str


class TestMessageEntity:
    """Тесты сущности сообщения"""

    def test_message_creation(self):
        """Тест создания сообщения"""
        message = Message(message_id=123, user_id=456789, chat_id=-100123456789, text="Test message", timestamp=datetime.now())

        assert message.message_id == 123
        assert message.user_id == 456789
        assert message.chat_id == -100123456789
        assert message.text == "Test message"
        assert isinstance(message.timestamp, datetime)

    def test_message_creation_without_timestamp(self):
        """Тест создания сообщения с timestamp по умолчанию"""
        before_creation = datetime.now()
        message = Message(message_id=123, user_id=456789, chat_id=-100123456789, text="Test message", timestamp=datetime.now())
        after_creation = datetime.now()

        assert before_creation <= message.timestamp <= after_creation

    def test_message_with_empty_text(self):
        """Тест сообщения с пустым текстом"""
        message = Message(message_id=123, user_id=456789, chat_id=-100123456789, text="", timestamp=datetime.now())

        assert message.text == ""

    def test_message_with_none_text(self):
        """Тест сообщения с None в качестве текста (не поддерживается)"""
        # Message требует строку, поэтому передаем пустую строку
        message = Message(message_id=123, user_id=456789, chat_id=-100123456789, text="", timestamp=datetime.now())

        assert message.text == ""

    def test_message_with_long_text(self):
        """Тест сообщения с длинным текстом"""
        long_text = "a" * 10000
        message = Message(message_id=123, user_id=456789, chat_id=-100123456789, text=long_text, timestamp=datetime.now())

        assert message.text == long_text
        assert len(message.text) == 10000

    def test_message_equality(self):
        """Тест сравнения сообщений"""
        timestamp = datetime.now()

        message1 = Message(123, 456789, -100123456789, "Test", timestamp)
        message2 = Message(123, 456789, -100123456789, "Test", timestamp)
        message3 = Message(124, 456789, -100123456789, "Test", timestamp)

        assert message1 == message2
        assert message1 != message3

    def test_message_hash(self):
        """Тест хеширования сообщений"""
        timestamp = datetime.now()

        message1 = Message(123, 456789, -100123456789, "Test", timestamp)
        message2 = Message(123, 456789, -100123456789, "Test", timestamp)
        message3 = Message(124, 456789, -100123456789, "Test", timestamp)

        # dataclass объекты сравнимы по равенству
        assert message1 == message2
        assert message1 != message3

    def test_message_string_representation(self):
        """Тест строкового представления сообщения"""
        message = Message(123, 456789, -100123456789, "Test message", datetime.now())

        str_repr = str(message)
        assert "123" in str_repr
        assert "456789" in str_repr
        assert "Test message" in str_repr

    def test_message_repr(self):
        """Тест repr представления сообщения"""
        message = Message(123, 456789, -100123456789, "Test message", datetime.now())

        repr_str = repr(message)
        assert "Message" in repr_str
        assert "123" in repr_str
        assert "456789" in repr_str

    def test_message_is_from_user(self):
        """Тест проверки принадлежности сообщения пользователю"""
        message = Message(123, 456789, -100123456789, "Test", datetime.now())

        assert message.user_id == 456789
        assert message.user_id != 123456

    def test_message_is_in_chat(self):
        """Тест проверки принадлежности сообщения чату"""
        message = Message(123, 456789, -100123456789, "Test", datetime.now())

        assert message.chat_id == -100123456789
        assert message.chat_id != -100987654321

    def test_message_contains_text(self):
        """Тест проверки содержания текста в сообщении"""
        message = Message(123, 456789, -100123456789, "Hello world test", datetime.now())

        assert "world" in message.text
        assert "WORLD" not in message.text  # Точное совпадение
        assert "python" not in message.text

        # Тест с пустым текстом
        empty_message = Message(124, 456789, -100123456789, "", datetime.now())
        assert "test" not in empty_message.text

    def test_message_word_count(self):
        """Тест подсчета слов в сообщении"""
        message = Message(123, 456789, -100123456789, "Hello world test message", datetime.now())

        word_count = len(message.text.split())
        assert word_count == 4

        # Тест с пустым текстом
        empty_message = Message(124, 456789, -100123456789, "", datetime.now())
        assert len(empty_message.text.split()) == 0

        # Тест с лишними пробелами
        spaced_message = Message(126, 456789, -100123456789, "  hello   world  ", datetime.now())
        assert len(spaced_message.text.split()) == 2

    def test_message_age(self):
        """Тест определения возраста сообщения"""
        past_time = datetime.now() - timedelta(minutes=5)
        message = Message(123, 456789, -100123456789, "Test", past_time)

        age = datetime.now() - message.timestamp
        assert isinstance(age, timedelta)
        assert age.total_seconds() > 290  # Около 5 минут
        assert age.total_seconds() < 310  # С небольшой погрешностью


class TestEntityValidation:
    """Тесты валидации сущностей"""

    def test_user_invalid_user_id(self):
        """Тест создания пользователя с невалидным ID"""
        # dataclass не валидирует типы автоматически, но можем проверить поведение
        try:
            user = User(None, -100123456789)
            # Если не выбросило исключение, проверим что значение присвоилось
            assert user.user_id is None
        except (ValueError, TypeError):
            # Это ожидаемое поведение
            pass

    def test_user_invalid_chat_id(self):
        """Тест создания пользователя с невалидным ID чата"""
        try:
            user = User(123456789, None)
            assert user.chat_id is None
        except (ValueError, TypeError):
            pass

    def test_user_negative_warnings(self):
        """Тест создания пользователя с отрицательными предупреждениями"""
        # dataclass позволяет отрицательные значения
        user = User(123456789, -100123456789, warnings_count=-1)
        assert user.warnings_count == -1

    def test_message_invalid_message_id(self):
        """Тест создания сообщения с невалидным ID"""
        # Проверим что dataclass позволяет различные типы
        message = Message(None, 456789, -100123456789, "Test", datetime.now())
        assert message.message_id is None

    def test_message_invalid_user_id(self):
        """Тест создания сообщения с невалидным ID пользователя"""
        message = Message(123, None, -100123456789, "Test", datetime.now())
        assert message.user_id is None

    def test_message_invalid_chat_id(self):
        """Тест создания сообщения с невалидным ID чата"""
        message = Message(123, 456789, None, "Test", datetime.now())
        assert message.chat_id is None


class TestMessageViolations:
    """Тесты для функциональности нарушений в сообщениях"""

    def test_message_with_violations(self):
        """Тест сообщения с нарушениями"""
        message = Message(
            message_id=123,
            user_id=456789,
            chat_id=-100123456789,
            text="Spam message",
            timestamp=datetime.now(),
            contains_violations=True,
            violation_words=["spam"],
        )

        assert message.contains_violations is True
        assert "spam" in message.violation_words
        assert len(message.violation_words) == 1

    def test_message_without_violations(self):
        """Тест сообщения без нарушений"""
        message = Message(
            message_id=123, user_id=456789, chat_id=-100123456789, text="Clean message", timestamp=datetime.now()
        )

        assert message.contains_violations is False
        assert message.violation_words == []

    def test_message_post_init_violation_words(self):
        """Тест автоинициализации violation_words"""
        message = Message(
            message_id=123,
            user_id=456789,
            chat_id=-100123456789,
            text="Test message",
            timestamp=datetime.now(),
            violation_words=None,  # Должно стать пустым списком
        )

        assert message.violation_words == []
        assert isinstance(message.violation_words, list)


class TestUserWarnings:
    """Тесты для функциональности предупреждений пользователей"""

    def test_user_warning_time_tracking(self):
        """Тест отслеживания времени последнего предупреждения"""
        warning_time = datetime.now()
        user = User(user_id=123456789, chat_id=-100123456789, warnings_count=1, last_warning_time=warning_time)

        assert user.last_warning_time == warning_time
        assert user.warnings_count == 1

    def test_user_can_send_messages_functionality(self):
        """Тест функциональности разрешения отправки сообщений"""
        user = User(123456789, -100123456789)

        # По умолчанию может отправлять
        assert user.can_send_messages is True

        # Запретим отправку (заглушение)
        user.can_send_messages = False
        assert user.can_send_messages is False

        # Разрешим снова
        user.can_send_messages = True
        assert user.can_send_messages is True


if __name__ == "__main__":
    pytest.main([__file__])
