"""
Тесты для системы авторизации бота
"""
from unittest.mock import AsyncMock, Mock, patch

import pytest

from application.settings import AuthConfig
from interfaces.telegram.decorators import admin_only, chat_admin_only, get_user_role, is_user_authorized, owner_only


@pytest.fixture
def mock_config():
    """Фикстура для мока конфигурации"""
    with patch("interfaces.telegram.decorators.get_config") as mock_get_config:
        mock_config = Mock()
        mock_config.auth.owner_id = 123
        mock_config.auth.admin_ids = [456, 789]
        mock_get_config.return_value = mock_config
        yield mock_config


@pytest.fixture
def mock_message():
    """Фикстура для мока сообщения Telegram"""
    message = Mock()
    message.from_user.id = 999888777
    message.chat.id = -100123456789
    message.reply = AsyncMock()
    message.bot.get_chat_member = AsyncMock()
    return message


class TestAuthorizationDecorators:
    """Тесты декораторов авторизации"""

    @pytest.mark.asyncio
    async def test_owner_only_success(self, mock_config, mock_message):
        """Тест успешного доступа владельца"""
        mock_message.from_user.id = 123  # Owner ID (совпадает с mock_config)

        @owner_only
        async def test_command(self, message):
            return "success"

        # Создаем mock объект self
        mock_self = Mock()
        result = await test_command(mock_self, mock_message)

        assert result == "success"
        mock_message.reply.assert_not_called()

    @pytest.mark.asyncio
    async def test_owner_only_denied(self, mock_config, mock_message):
        """Тест отказа в доступе не-владельцу"""
        mock_message.from_user.id = 999888777  # Not owner

        @owner_only
        async def test_command(self, message):
            return "success"

        mock_self = Mock()
        result = await test_command(mock_self, mock_message)

        assert result is None
        mock_message.reply.assert_called_once_with("🚫 Эта команда доступна только владельцу бота.")

    @pytest.mark.asyncio
    async def test_admin_only_owner_access(self, mock_config, mock_message):
        """Тест доступа владельца к админским командам"""
        mock_message.from_user.id = 123  # Owner ID (совпадает с mock_config)

        @admin_only
        async def test_command(self, message):
            return "success"

        mock_self = Mock()
        result = await test_command(mock_self, mock_message)

        assert result == "success"
        mock_message.reply.assert_not_called()

    @pytest.mark.asyncio
    async def test_admin_only_admin_access(self, mock_config, mock_message):
        """Тест доступа администратора к админским командам"""
        mock_message.from_user.id = 456  # Admin ID (совпадает с mock_config)

        @admin_only
        async def test_command(self, message):
            return "success"

        mock_self = Mock()
        result = await test_command(mock_self, mock_message)

        assert result == "success"
        mock_message.reply.assert_not_called()

    @pytest.mark.asyncio
    async def test_admin_only_denied(self, mock_config, mock_message):
        """Тест отказа в доступе обычному пользователю"""
        mock_message.from_user.id = 999888777  # Regular user

        @admin_only
        async def test_command(self, message):
            return "success"

        mock_self = Mock()
        result = await test_command(mock_self, mock_message)

        assert result is None
        mock_message.reply.assert_called_once_with("🚫 Эта команда доступна только администраторам бота.")

    @pytest.mark.asyncio
    async def test_chat_admin_only_chat_admin_access(self, mock_config, mock_message):
        """Тест доступа администратора чата"""
        mock_message.from_user.id = 999888777  # Regular user but chat admin

        # Мок для администратора чата
        chat_member = Mock()
        chat_member.status = "administrator"
        mock_message.bot.get_chat_member.return_value = chat_member

        @chat_admin_only
        async def test_command(self, message):
            return "success"

        mock_self = Mock()
        result = await test_command(mock_self, mock_message)

        assert result == "success"
        mock_message.reply.assert_not_called()
        mock_message.bot.get_chat_member.assert_called_once_with(
            chat_id=mock_message.chat.id, user_id=mock_message.from_user.id
        )

    @pytest.mark.asyncio
    async def test_chat_admin_only_creator_access(self, mock_config, mock_message):
        """Тест доступа создателя чата"""
        mock_message.from_user.id = 999888777  # Regular user but chat creator

        # Мок для создателя чата
        chat_member = Mock()
        chat_member.status = "creator"
        mock_message.bot.get_chat_member.return_value = chat_member

        @chat_admin_only
        async def test_command(self, message):
            return "success"

        mock_self = Mock()
        result = await test_command(mock_self, mock_message)

        assert result == "success"
        mock_message.reply.assert_not_called()

    @pytest.mark.asyncio
    async def test_chat_admin_only_denied(self, mock_config, mock_message):
        """Тест отказа в доступе обычному участнику чата"""
        mock_message.from_user.id = 999888777  # Regular user

        # Мок для обычного участника
        chat_member = Mock()
        chat_member.status = "member"
        mock_message.bot.get_chat_member.return_value = chat_member

        @chat_admin_only
        async def test_command(self, message):
            return "success"

        mock_self = Mock()
        result = await test_command(mock_self, mock_message)

        assert result is None
        mock_message.reply.assert_called_once_with("🚫 Эта команда доступна только администраторам чата.")


class TestAuthorizationHelpers:
    """Тесты вспомогательных функций авторизации"""

    @pytest.mark.asyncio
    async def test_is_user_authorized_owner(self, mock_config):
        """Тест авторизации владельца"""
        result = await is_user_authorized(123, "owner")  # Owner ID = 123
        assert result is True

        result = await is_user_authorized(123, "admin")
        assert result is True

        result = await is_user_authorized(123, "chat_admin")
        assert result is True

    @pytest.mark.asyncio
    async def test_is_user_authorized_admin(self, mock_config):
        """Тест авторизации администратора"""
        result = await is_user_authorized(456, "owner")  # Admin ID = 456
        assert result is False

        result = await is_user_authorized(456, "admin")
        assert result is True

        result = await is_user_authorized(456, "chat_admin")
        assert result is True

    @pytest.mark.asyncio
    async def test_is_user_authorized_chat_admin(self, mock_config):
        """Тест авторизации администратора чата"""
        mock_bot = Mock()
        chat_member = Mock()
        chat_member.status = "administrator"
        mock_bot.get_chat_member = AsyncMock(return_value=chat_member)

        result = await is_user_authorized(999, "chat_admin", chat_id=-100123456789, bot=mock_bot)
        assert result is True

        # Обычный участник
        chat_member.status = "member"
        result = await is_user_authorized(999, "chat_admin", chat_id=-100123456789, bot=mock_bot)
        assert result is False

    def test_get_user_role(self, mock_config):
        """Тест определения роли пользователя"""
        assert get_user_role(123) == "owner"  # Owner ID = 123
        assert get_user_role(456) == "admin"  # Admin ID = 456
        assert get_user_role(789) == "admin"  # Admin ID = 789
        assert get_user_role(999) == "user"  # Regular user


@pytest.mark.asyncio
async def test_chat_member_api_error_handling(mock_config, mock_message):
    """Тест обработки ошибок API Telegram при проверке прав в чате"""
    mock_message.from_user.id = 999888777  # Regular user
    mock_message.bot.get_chat_member.side_effect = Exception("API Error")

    @chat_admin_only
    async def test_command(self, message):
        return "success"

    mock_self = Mock()
    result = await test_command(mock_self, mock_message)

    assert result is None
    mock_message.reply.assert_called_once_with("❌ Не удалось проверить права доступа в чате.")


if __name__ == "__main__":
    pytest.main([__file__])
