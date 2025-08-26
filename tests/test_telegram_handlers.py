from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest

from domain.entities.message import Message
from domain.entities.user import User


@pytest.fixture(autouse=True)
def mock_decorators():
    """Автоматически мокает декораторы для всех тестов в этом модуле"""

    def mock_decorator(func):
        """Пустой декоратор, который просто возвращает функцию"""
        return func

    # Патчим декораторы в модуле handlers
    with patch("interfaces.telegram.handlers.admin_only", mock_decorator), patch(
        "interfaces.telegram.handlers.chat_admin_only", mock_decorator
    ), patch("interfaces.telegram.handlers.owner_only", mock_decorator):
        yield


@pytest.fixture
def mock_moderation_service():
    """Mock сервиса модерации"""
    service = AsyncMock()
    service.check_message.return_value = []
    service.ban_user = AsyncMock()
    service.unban_user = AsyncMock()
    service.mute_user = AsyncMock()
    service.unmute_user = AsyncMock()
    service.kick_user = AsyncMock()
    service.set_warnings_limit = AsyncMock()
    service.add_forbidden_word = AsyncMock()
    service.remove_forbidden_word = AsyncMock(return_value=True)
    service.get_forbidden_words = AsyncMock(return_value=["bad", "word"])
    service.clear_forbidden_words = AsyncMock()
    service.get_warnings_limit = AsyncMock(return_value=3)
    return service


@pytest.fixture
def mock_user_repository():
    """Mock репозитория пользователей"""
    repo = AsyncMock()
    mock_user = User(user_id=123, chat_id=456)
    repo.get_by_id.return_value = mock_user
    repo.get_or_create.return_value = mock_user
    return repo


@pytest.fixture
def handlers(mock_moderation_service, mock_user_repository):
    """Экземпляр обработчиков команд"""
    from interfaces.telegram.handlers import ModeratorCommandHandlers

    # Создаем экземпляр
    instance = ModeratorCommandHandlers(moderation_service=mock_moderation_service, user_repository=mock_user_repository)

    # Сохраняем оригинальные методы
    original_methods = {}

    # Функции, которые нужно "раздекорировать"
    decorated_methods = [
        "add_forbidden_word_command",
        "remove_forbidden_word_command",
        "list_forbidden_words_command",
        "set_warnings_limit_command",
        "ban_command",
        "unban_command",
        "mute_command",
        "unmute_command",
        "kick_command",
        "bot_status_command",
    ]

    # Убираем декораторы, заменяя методы их исходными функциями
    for method_name in decorated_methods:
        if hasattr(instance, method_name):
            # Получаем оригинальную функцию из декорированного метода
            method = getattr(instance, method_name)
            # Пытаемся получить __wrapped__ если есть (это оригинальная функция)
            if hasattr(method, "__wrapped__"):
                original_methods[method_name] = method.__wrapped__
                setattr(instance, method_name, original_methods[method_name].__get__(instance))

    return instance


@pytest.fixture
def mock_telegram_message():
    """Mock объекта сообщения Telegram"""
    message = Mock()
    message.message_id = 789
    message.text = "test message"
    message.reply = AsyncMock()
    message.delete = AsyncMock()
    message.from_user = Mock()
    message.from_user.id = 123
    message.from_user.username = "testuser"
    message.chat = Mock()
    message.chat.id = 456
    message.chat.type = "supergroup"
    message.bot = AsyncMock()
    message.bot.id = 987654321  # ID бота
    message.bot.get_chat_member = AsyncMock()
    message.bot.ban_chat_member = AsyncMock()
    message.bot.unban_chat_member = AsyncMock()
    message.bot.restrict_chat_member = AsyncMock()
    message.reply_to_message = None
    return message


class TestMessageHandler:
    @pytest.mark.asyncio
    async def test_handle_message_no_violations(self, handlers, mock_telegram_message, mock_moderation_service):
        """Тест обработки сообщения без нарушений"""
        mock_moderation_service.check_message.return_value = []

        await handlers.handle_message(mock_telegram_message)

        mock_moderation_service.check_message.assert_awaited_once()
        mock_telegram_message.reply.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_handle_message_with_violations(self, handlers, mock_telegram_message, mock_moderation_service):
        """Тест обработки сообщения с нарушениями"""
        mock_moderation_service.check_message.return_value = ["bad", "word"]

        await handlers.handle_message(mock_telegram_message)

        mock_moderation_service.check_message.assert_awaited_once()
        mock_telegram_message.reply.assert_awaited_once()
        args = mock_telegram_message.reply.call_args[0][0]
        assert "запрещенные слова" in args
        assert "bad" in args
        assert "word" in args

    @pytest.mark.asyncio
    async def test_handle_message_no_text(self, handlers, mock_telegram_message):
        """Тест обработки сообщения без текста"""
        mock_telegram_message.text = None

        await handlers.handle_message(mock_telegram_message)

        # Сообщение без текста не должно обрабатываться


class TestBanCommand:
    @pytest.mark.asyncio
    async def test_ban_command_success(self, handlers, mock_telegram_message, mock_moderation_service):
        """Тест успешной команды бана"""
        # Настраиваем reply_to_message
        reply_message = Mock()
        reply_message.from_user = Mock()
        reply_message.from_user.id = 999
        mock_telegram_message.reply_to_message = reply_message

        # Мокаем получение прав администратора чата
        chat_member = Mock()
        chat_member.status = "administrator"
        mock_telegram_message.bot.get_chat_member.return_value = chat_member

        await handlers.ban_command(mock_telegram_message)

        mock_moderation_service.ban_user.assert_awaited_once()
        mock_telegram_message.bot.ban_chat_member.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_ban_command_no_reply(self, handlers, mock_telegram_message):
        """Тест команды бана без ответа на сообщение"""
        mock_telegram_message.reply_to_message = None

        # Мокаем получение прав администратора чата
        chat_member = Mock()
        chat_member.status = "administrator"
        mock_telegram_message.bot.get_chat_member.return_value = chat_member

        await handlers.ban_command(mock_telegram_message)

        mock_telegram_message.reply.assert_awaited()
        # Проверяем что есть сообщение об ошибке использования команды
        args = mock_telegram_message.reply.call_args[0][0]
        assert any(phrase in args for phrase in ["ответ", "сообщение", "команда должна использоваться"])

    @pytest.mark.asyncio
    async def test_ban_command_bot_target(self, handlers, mock_telegram_message):
        """Тест команды бана на самого бота"""
        reply_message = Mock()
        reply_message.from_user = Mock()
        reply_message.from_user.id = 987654321  # ID бота
        mock_telegram_message.reply_to_message = reply_message

        # Мокаем получение прав администратора чата
        chat_member = Mock()
        chat_member.status = "administrator"
        mock_telegram_message.bot.get_chat_member.return_value = chat_member

        await handlers.ban_command(mock_telegram_message)

        mock_telegram_message.reply.assert_awaited()
        args = mock_telegram_message.reply.call_args[0][0]
        assert any(phrase in args for phrase in ["не могу модерировать", "сам себя"])


class TestUnbanCommand:
    @pytest.mark.asyncio
    async def test_unban_command_success(self, handlers, mock_telegram_message, mock_moderation_service):
        """Тест успешной команды разбана"""
        reply_message = Mock()
        reply_message.from_user = Mock()
        reply_message.from_user.id = 999
        mock_telegram_message.reply_to_message = reply_message

        # Мокаем получение прав администратора чата
        chat_member = Mock()
        chat_member.status = "administrator"
        mock_telegram_message.bot.get_chat_member.return_value = chat_member

        await handlers.unban_command(mock_telegram_message)

        mock_moderation_service.unban_user.assert_awaited_once()
        mock_telegram_message.bot.unban_chat_member.assert_awaited_once()


class TestMuteCommand:
    @pytest.mark.asyncio
    async def test_mute_command_success(self, handlers, mock_telegram_message, mock_moderation_service):
        """Тест успешной команды заглушения"""
        reply_message = Mock()
        reply_message.from_user = Mock()
        reply_message.from_user.id = 999
        mock_telegram_message.reply_to_message = reply_message

        # Мокаем получение прав администратора чата
        chat_member = Mock()
        chat_member.status = "administrator"
        mock_telegram_message.bot.get_chat_member.return_value = chat_member

        await handlers.mute_command(mock_telegram_message)

        mock_moderation_service.mute_user.assert_awaited_once()
        mock_telegram_message.bot.restrict_chat_member.assert_awaited_once()


class TestForbiddenWordsCommands:
    @pytest.mark.asyncio
    async def test_add_forbidden_word_success(self, handlers, mock_telegram_message, mock_moderation_service):
        """Тест добавления запрещенного слова"""
        mock_telegram_message.text = "/add_forbidden badword"

        await handlers.add_forbidden_word_command(mock_telegram_message)

        mock_moderation_service.add_forbidden_word.assert_awaited_once_with("badword")
        mock_telegram_message.reply.assert_awaited_once()
        args = mock_telegram_message.reply.call_args[0][0]
        assert "добавлено" in args and "badword" in args

    @pytest.mark.asyncio
    async def test_add_forbidden_word_no_args(self, handlers, mock_telegram_message):
        """Тест добавления запрещенного слова без аргументов"""
        mock_telegram_message.text = "/add_forbidden"

        await handlers.add_forbidden_word_command(mock_telegram_message)

        mock_telegram_message.reply.assert_awaited_once()
        args = mock_telegram_message.reply.call_args[0][0]
        assert "укажите слово" in args

    @pytest.mark.asyncio
    async def test_remove_forbidden_word_success(self, handlers, mock_telegram_message, mock_moderation_service):
        """Тест удаления запрещенного слова"""
        mock_telegram_message.text = "/remove_forbidden badword"
        mock_moderation_service.remove_forbidden_word.return_value = True

        await handlers.remove_forbidden_word_command(mock_telegram_message)

        mock_moderation_service.remove_forbidden_word.assert_awaited_once_with("badword")
        mock_telegram_message.reply.assert_awaited_once()
        args = mock_telegram_message.reply.call_args[0][0]
        assert "удалено" in args

    @pytest.mark.asyncio
    async def test_remove_forbidden_word_not_found(self, handlers, mock_telegram_message, mock_moderation_service):
        """Тест удаления несуществующего запрещенного слова"""
        mock_telegram_message.text = "/remove_forbidden nonexistent"
        mock_moderation_service.remove_forbidden_word.return_value = False

        await handlers.remove_forbidden_word_command(mock_telegram_message)

        mock_telegram_message.reply.assert_awaited_once()
        args = mock_telegram_message.reply.call_args[0][0]
        assert "не найдено" in args

    @pytest.mark.asyncio
    async def test_list_forbidden_words_with_words(self, handlers, mock_telegram_message, mock_moderation_service):
        """Тест показа списка запрещенных слов"""
        mock_moderation_service.get_forbidden_words.return_value = ["bad", "word", "spam"]

        await handlers.list_forbidden_words_command(mock_telegram_message)

        mock_telegram_message.reply.assert_awaited_once()
        args = mock_telegram_message.reply.call_args[0][0]
        assert "bad" in args
        assert "word" in args
        assert "spam" in args

    @pytest.mark.asyncio
    async def test_list_forbidden_words_empty(self, handlers, mock_telegram_message, mock_moderation_service):
        """Тест показа пустого списка запрещенных слов"""
        mock_moderation_service.get_forbidden_words.return_value = []

        await handlers.list_forbidden_words_command(mock_telegram_message)

        mock_telegram_message.reply.assert_awaited_once()
        args = mock_telegram_message.reply.call_args[0][0]
        assert "пуст" in args


class TestConfigurationCommands:
    @pytest.mark.asyncio
    async def test_set_warnings_limit_success(self, handlers, mock_telegram_message, mock_moderation_service):
        """Тест установки лимита предупреждений"""
        mock_telegram_message.text = "/set_warnings 5"

        await handlers.set_warnings_limit_command(mock_telegram_message)

        mock_moderation_service.set_warnings_limit.assert_awaited_once_with(456, 5)
        mock_telegram_message.reply.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_set_warnings_limit_invalid_args(self, handlers, mock_telegram_message):
        """Тест установки лимита предупреждений с неверными аргументами"""
        mock_telegram_message.text = "/set_warnings abc"

        await handlers.set_warnings_limit_command(mock_telegram_message)

        mock_telegram_message.reply.assert_awaited_once()
        args = mock_telegram_message.reply.call_args[0][0]
        assert "укажите лимит" in args

    @pytest.mark.asyncio
    async def test_set_warnings_limit_negative(self, handlers, mock_telegram_message):
        """Тест установки отрицательного лимита предупреждений"""
        mock_telegram_message.text = "/set_warnings -1"

        await handlers.set_warnings_limit_command(mock_telegram_message)

        mock_telegram_message.reply.assert_awaited_once()
        args = mock_telegram_message.reply.call_args[0][0]
        # -1 не проходит валидацию isdigit(), поэтому возвращается сообщение об ошибке формата
        assert "укажите лимит" in args


class TestHelpCommand:
    @pytest.mark.asyncio
    async def test_help_command_admin(self, handlers, mock_telegram_message):
        """Тест команды помощи для администратора"""
        # Мокаем получение роли пользователя
        with patch("interfaces.telegram.decorators.get_config") as mock_get_config:
            mock_config = Mock()
            mock_config.auth.owner_id = 999  # Другой ID
            mock_config.auth.admin_ids = [123]  # ID текущего пользователя
            mock_get_config.return_value = mock_config

            await handlers.help_command(mock_telegram_message)

            mock_telegram_message.reply.assert_awaited_once()
            args = mock_telegram_message.reply.call_args[0][0]
            assert "администратора" in args
            assert "/add_forbidden" in args

    @pytest.mark.asyncio
    async def test_help_command_owner(self, handlers, mock_telegram_message):
        """Тест команды помощи для владельца"""
        # Мокаем получение роли пользователя
        with patch("interfaces.telegram.decorators.get_config") as mock_get_config:
            mock_config = Mock()
            mock_config.auth.owner_id = 123  # ID текущего пользователя
            mock_config.auth.admin_ids = []
            mock_get_config.return_value = mock_config

            await handlers.help_command(mock_telegram_message)

            mock_telegram_message.reply.assert_awaited_once()
            args = mock_telegram_message.reply.call_args[0][0]
            assert "владельца" in args
            assert "/clear_forbidden" in args

    @pytest.mark.asyncio
    async def test_help_command_regular_user(self, handlers, mock_telegram_message):
        """Тест команды помощи для обычного пользователя"""
        # Мокаем получение роли пользователя
        with patch("interfaces.telegram.decorators.get_config") as mock_get_config:
            mock_config = Mock()
            mock_config.auth.owner_id = 999  # Другой ID
            mock_config.auth.admin_ids = []  # Текущий пользователь не админ
            mock_get_config.return_value = mock_config

            await handlers.help_command(mock_telegram_message)

            mock_telegram_message.reply.assert_awaited_once()
            args = mock_telegram_message.reply.call_args[0][0]
            assert "Общие команды" in args


class TestBotStatusCommand:
    @pytest.mark.asyncio
    async def test_bot_status_command(self, handlers, mock_telegram_message, mock_moderation_service):
        """Тест команды статуса бота"""
        mock_moderation_service.get_warnings_limit.return_value = 3
        mock_moderation_service.get_forbidden_words.return_value = ["bad", "word"]

        # Мокируем get_config и get_user_role внутри метода
        with patch("application.settings.get_config") as mock_get_config_settings:
            with patch("interfaces.telegram.decorators.get_user_role") as mock_get_user_role:
                mock_config = Mock()
                mock_config.environment = "test"
                mock_get_config_settings.return_value = mock_config
                mock_get_user_role.return_value = "admin"

                await handlers.bot_status_command(mock_telegram_message)

                mock_telegram_message.reply.assert_awaited_once()
                args = mock_telegram_message.reply.call_args[0][0]
                assert "Статус бота" in args
                assert "3" in args  # warnings limit
                assert "2" in args  # forbidden words count


class TestKickCommand:
    @pytest.mark.asyncio
    async def test_kick_command_success(self, handlers, mock_telegram_message, mock_moderation_service):
        """Тест успешной команды исключения"""
        reply_message = Mock()
        reply_message.from_user = Mock()
        reply_message.from_user.id = 999
        reply_message.from_user.username = "testuser"
        mock_telegram_message.reply_to_message = reply_message

        await handlers.kick_command(mock_telegram_message)

        mock_telegram_message.reply.assert_awaited_once()
        assert "исключен" in mock_telegram_message.reply.call_args[0][0]


class TestUtilityMethods:
    @pytest.mark.asyncio
    async def test_get_target_user_success(self, handlers, mock_telegram_message, mock_user_repository):
        """Тест получения целевого пользователя"""
        reply_message = Mock()
        reply_message.from_user = Mock()
        reply_message.from_user.id = 999
        mock_telegram_message.reply_to_message = reply_message

        result = await handlers._get_target_user(mock_telegram_message)

        assert result is not None
        mock_user_repository.get_by_id.assert_awaited_once_with(999, 456)

    @pytest.mark.asyncio
    async def test_get_target_user_no_reply(self, handlers, mock_telegram_message):
        """Тест получения целевого пользователя без ответа"""
        mock_telegram_message.reply_to_message = None

        result = await handlers._get_target_user(mock_telegram_message)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_target_user_bot_id(self, handlers, mock_telegram_message):
        """Тест получения целевого пользователя когда цель - сам бот"""
        reply_message = Mock()
        reply_message.from_user = Mock()
        reply_message.from_user.id = 123456789
        mock_telegram_message.reply_to_message = reply_message
        mock_telegram_message.bot.id = 123456789

        result = await handlers._get_target_user(mock_telegram_message)

        assert result is None
        mock_telegram_message.reply.assert_awaited_once()
        args = mock_telegram_message.reply.call_args[0][0]
        assert "не могу модерировать сам себя" in args
