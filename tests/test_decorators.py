"""
Тесты для декораторов авторизации
"""
from unittest.mock import AsyncMock, Mock, patch

import pytest

from interfaces.telegram.decorators import (
    admin_only,
    admin_required,
    chat_admin_only,
    get_user_role,
    is_user_authorized,
    owner_only,
    owner_required,
    require_role,
)


class TestAuthorizationDecorators:
    """Тесты декораторов авторизации"""

    @pytest.fixture
    def mock_message(self):
        """Мок сообщения Telegram"""
        message = Mock()
        message.from_user = Mock()
        message.from_user.id = 123456789
        message.chat = Mock()
        message.chat.id = -100123456789
        message.reply = AsyncMock()
        message.bot = Mock()
        message.bot.get_chat_member = AsyncMock()
        return message

    @pytest.fixture
    def mock_config(self):
        """Мок конфигурации"""
        config = Mock()
        config.auth = Mock()
        config.auth.owner_id = 999888777
        config.auth.admin_ids = [111222333, 444555666]
        return config

    @pytest.fixture
    def mock_handler_self(self):
        """Мок self для методов обработчика"""
        return Mock()

    @pytest.mark.asyncio
    async def test_owner_only_success(self, mock_message, mock_config, mock_handler_self):
        """Тест успешной проверки владельца"""
        mock_message.from_user.id = 999888777  # owner

        @owner_only
        async def test_handler(self, message):
            return "owner_success"

        with patch("interfaces.telegram.decorators.get_config", return_value=mock_config):
            result = await test_handler(mock_handler_self, mock_message)
            assert result == "owner_success"

    @pytest.mark.asyncio
    async def test_owner_only_unauthorized(self, mock_message, mock_config, mock_handler_self):
        """Тест неавторизованного доступа к команде владельца"""
        mock_message.from_user.id = 123456789  # user

        @owner_only
        async def test_handler(self, message):
            return "owner_success"

        with patch("interfaces.telegram.decorators.get_config", return_value=mock_config):
            result = await test_handler(mock_handler_self, mock_message)
            assert result is None

            mock_message.reply.assert_called_once_with("🚫 Эта команда доступна только владельцу бота.")

    @pytest.mark.asyncio
    async def test_admin_only_owner_success(self, mock_message, mock_config, mock_handler_self):
        """Тест что владелец может выполнять команды администратора"""
        mock_message.from_user.id = 999888777  # owner

        @admin_only
        async def test_handler(self, message):
            return "admin_success"

        with patch("interfaces.telegram.decorators.get_config", return_value=mock_config):
            result = await test_handler(mock_handler_self, mock_message)
            assert result == "admin_success"

    @pytest.mark.asyncio
    async def test_admin_only_admin_success(self, mock_message, mock_config, mock_handler_self):
        """Тест успешной проверки администратора"""
        mock_message.from_user.id = 111222333  # admin

        @admin_only
        async def test_handler(self, message):
            return "admin_success"

        with patch("interfaces.telegram.decorators.get_config", return_value=mock_config):
            result = await test_handler(mock_handler_self, mock_message)
            assert result == "admin_success"

    @pytest.mark.asyncio
    async def test_admin_only_unauthorized(self, mock_message, mock_config, mock_handler_self):
        """Тест неавторизованного доступа к команде администратора"""
        mock_message.from_user.id = 123456789  # user

        @admin_only
        async def test_handler(self, message):
            return "admin_success"

        with patch("interfaces.telegram.decorators.get_config", return_value=mock_config):
            result = await test_handler(mock_handler_self, mock_message)
            assert result is None

            mock_message.reply.assert_called_once_with("🚫 Эта команда доступна только администраторам бота.")

    @pytest.mark.asyncio
    async def test_chat_admin_only_owner_success(self, mock_message, mock_config, mock_handler_self):
        """Тест что владелец может выполнять команды администратора чата"""
        mock_message.from_user.id = 999888777  # owner

        @chat_admin_only
        async def test_handler(self, message):
            return "chat_admin_success"

        with patch("interfaces.telegram.decorators.get_config", return_value=mock_config):
            result = await test_handler(mock_handler_self, mock_message)
            assert result == "chat_admin_success"

    @pytest.mark.asyncio
    async def test_chat_admin_only_bot_admin_success(self, mock_message, mock_config, mock_handler_self):
        """Тест что администратор бота может выполнять команды администратора чата"""
        mock_message.from_user.id = 111222333  # admin

        @chat_admin_only
        async def test_handler(self, message):
            return "chat_admin_success"

        with patch("interfaces.telegram.decorators.get_config", return_value=mock_config):
            result = await test_handler(mock_handler_self, mock_message)
            assert result == "chat_admin_success"

    @pytest.mark.asyncio
    async def test_chat_admin_only_chat_admin_success(self, mock_message, mock_config, mock_handler_self):
        """Тест успешной проверки администратора чата"""
        mock_message.from_user.id = 123456789  # user

        # Мокаем ответ get_chat_member
        chat_member = Mock()
        chat_member.status = "administrator"
        mock_message.bot.get_chat_member.return_value = chat_member

        @chat_admin_only
        async def test_handler(self, message):
            return "chat_admin_success"

        with patch("interfaces.telegram.decorators.get_config", return_value=mock_config):
            result = await test_handler(mock_handler_self, mock_message)
            assert result == "chat_admin_success"

    @pytest.mark.asyncio
    async def test_chat_admin_only_chat_creator_success(self, mock_message, mock_config, mock_handler_self):
        """Тест успешной проверки создателя чата"""
        mock_message.from_user.id = 123456789  # user

        # Мокаем ответ get_chat_member
        chat_member = Mock()
        chat_member.status = "creator"
        mock_message.bot.get_chat_member.return_value = chat_member

        @chat_admin_only
        async def test_handler(self, message):
            return "chat_admin_success"

        with patch("interfaces.telegram.decorators.get_config", return_value=mock_config):
            result = await test_handler(mock_handler_self, mock_message)
            assert result == "chat_admin_success"

    @pytest.mark.asyncio
    async def test_chat_admin_only_unauthorized(self, mock_message, mock_config, mock_handler_self):
        """Тест неавторизованного доступа к команде администратора чата"""
        mock_message.from_user.id = 123456789  # user

        # Мокаем ответ get_chat_member
        chat_member = Mock()
        chat_member.status = "member"
        mock_message.bot.get_chat_member.return_value = chat_member

        @chat_admin_only
        async def test_handler(self, message):
            return "chat_admin_success"

        with patch("interfaces.telegram.decorators.get_config", return_value=mock_config):
            result = await test_handler(mock_handler_self, mock_message)
            assert result is None

            mock_message.reply.assert_called_once_with("🚫 Эта команда доступна только администраторам чата.")

    @pytest.mark.asyncio
    async def test_chat_admin_only_get_chat_member_exception(self, mock_message, mock_config, mock_handler_self):
        """Тест обработки исключения при проверке прав в чате"""
        mock_message.from_user.id = 123456789  # user

        # Мокаем исключение в get_chat_member
        mock_message.bot.get_chat_member.side_effect = Exception("API Error")

        @chat_admin_only
        async def test_handler(self, message):
            return "chat_admin_success"

        with patch("interfaces.telegram.decorators.get_config", return_value=mock_config):
            result = await test_handler(mock_handler_self, mock_message)
            assert result is None

            mock_message.reply.assert_called_once_with("❌ Не удалось проверить права доступа в чате.")

    def test_get_user_role_owner(self, mock_config):
        """Тест определения роли владельца"""
        with patch("interfaces.telegram.decorators.get_config", return_value=mock_config):
            role = get_user_role(999888777)
            assert role == "owner"

    def test_get_user_role_admin(self, mock_config):
        """Тест определения роли администратора"""
        with patch("interfaces.telegram.decorators.get_config", return_value=mock_config):
            role = get_user_role(111222333)
            assert role == "admin"

    def test_get_user_role_user(self, mock_config):
        """Тест определения роли обычного пользователя"""
        with patch("interfaces.telegram.decorators.get_config", return_value=mock_config):
            role = get_user_role(123456789)
            assert role == "user"

    @pytest.mark.asyncio
    async def test_is_user_authorized_owner(self, mock_config):
        """Тест авторизации владельца для всех уровней"""
        with patch("interfaces.telegram.decorators.get_config", return_value=mock_config):
            assert await is_user_authorized(999888777, "owner") == True
            assert await is_user_authorized(999888777, "admin") == True
            assert await is_user_authorized(999888777, "chat_admin") == True

    @pytest.mark.asyncio
    async def test_is_user_authorized_admin(self, mock_config):
        """Тест авторизации администратора"""
        with patch("interfaces.telegram.decorators.get_config", return_value=mock_config):
            assert await is_user_authorized(111222333, "owner") == False
            assert await is_user_authorized(111222333, "admin") == True
            assert await is_user_authorized(111222333, "chat_admin") == True

    @pytest.mark.asyncio
    async def test_is_user_authorized_user(self, mock_config):
        """Тест авторизации обычного пользователя"""
        with patch("interfaces.telegram.decorators.get_config", return_value=mock_config):
            assert await is_user_authorized(123456789, "owner") == False
            assert await is_user_authorized(123456789, "admin") == False

    @pytest.mark.asyncio
    async def test_is_user_authorized_chat_admin_success(self, mock_config):
        """Тест авторизации администратора чата"""
        mock_bot = Mock()
        chat_member = Mock()
        chat_member.status = "administrator"
        mock_bot.get_chat_member = AsyncMock(return_value=chat_member)

        with patch("interfaces.telegram.decorators.get_config", return_value=mock_config):
            result = await is_user_authorized(123456789, "chat_admin", -100123456789, mock_bot)
            assert result == True

    @pytest.mark.asyncio
    async def test_is_user_authorized_chat_admin_creator(self, mock_config):
        """Тест авторизации создателя чата"""
        mock_bot = Mock()
        chat_member = Mock()
        chat_member.status = "creator"
        mock_bot.get_chat_member = AsyncMock(return_value=chat_member)

        with patch("interfaces.telegram.decorators.get_config", return_value=mock_config):
            result = await is_user_authorized(123456789, "chat_admin", -100123456789, mock_bot)
            assert result == True

    @pytest.mark.asyncio
    async def test_is_user_authorized_chat_admin_member(self, mock_config):
        """Тест отказа обычному члену чата"""
        mock_bot = Mock()
        chat_member = Mock()
        chat_member.status = "member"
        mock_bot.get_chat_member = AsyncMock(return_value=chat_member)

        with patch("interfaces.telegram.decorators.get_config", return_value=mock_config):
            result = await is_user_authorized(123456789, "chat_admin", -100123456789, mock_bot)
            assert result == False

    @pytest.mark.asyncio
    async def test_is_user_authorized_chat_admin_exception(self, mock_config):
        """Тест обработки исключения при проверке прав в чате"""
        mock_bot = Mock()
        mock_bot.get_chat_member = AsyncMock(side_effect=Exception("API Error"))

        with patch("interfaces.telegram.decorators.get_config", return_value=mock_config):
            result = await is_user_authorized(123456789, "chat_admin", -100123456789, mock_bot)
            assert result == False

    @pytest.mark.asyncio
    async def test_is_user_authorized_without_chat_id_and_bot(self, mock_config):
        """Тест проверки chat_admin без chat_id и bot"""
        with patch("interfaces.telegram.decorators.get_config", return_value=mock_config):
            # Обычный пользователь без права chat_admin, но без chat_id и bot
            result = await is_user_authorized(123456789, "chat_admin")
            assert result == False

    @pytest.mark.asyncio
    async def test_require_role_user_success(self, mock_message, mock_config):
        """Тест успешной проверки роли пользователя"""
        mock_message.from_user.id = 123456789  # user

        @require_role("user")
        async def test_handler(message):
            return "user_success"

        with patch("interfaces.telegram.decorators.get_config", return_value=mock_config):
            result = await test_handler(mock_message)
            assert result == "user_success"

    @pytest.mark.asyncio
    async def test_require_role_admin_success(self, mock_message, mock_config):
        """Тест успешной проверки роли администратора"""
        mock_message.from_user.id = 111222333  # admin

        @require_role("admin")
        async def test_handler(message):
            return "admin_success"

        with patch("interfaces.telegram.decorators.get_config", return_value=mock_config):
            result = await test_handler(mock_message)
            assert result == "admin_success"

    @pytest.mark.asyncio
    async def test_require_role_owner_can_access_admin(self, mock_message, mock_config):
        """Тест что владелец может выполнять команды администратора"""
        mock_message.from_user.id = 999888777  # owner

        @require_role("admin")
        async def test_handler(message):
            return "admin_success"

        with patch("interfaces.telegram.decorators.get_config", return_value=mock_config):
            result = await test_handler(mock_message)
            assert result == "admin_success"

    @pytest.mark.asyncio
    async def test_require_role_unauthorized(self, mock_message, mock_config):
        """Тест неавторизованного доступа"""
        mock_message.from_user.id = 123456789  # user

        @require_role("admin")
        async def test_handler(message):
            return "admin_success"

        with patch("interfaces.telegram.decorators.get_config", return_value=mock_config):
            result = await test_handler(mock_message)
            assert result is None

            mock_message.reply.assert_called_once_with("🚫 Эта команда доступна только для роли: admin")

    @pytest.mark.asyncio
    async def test_require_role_with_custom_message(self, mock_message, mock_config):
        """Тест кастомного сообщения об ошибке"""
        mock_message.from_user.id = 123456789  # user

        @require_role("admin", unauthorized_message="Только для администраторов!")
        async def test_handler(message):
            return "admin_success"

        with patch("interfaces.telegram.decorators.get_config", return_value=mock_config):
            result = await test_handler(mock_message)
            assert result is None

            mock_message.reply.assert_called_once_with("Только для администраторов!")

    @pytest.mark.asyncio
    async def test_admin_required_success(self, mock_message, mock_config):
        """Тест успешной проверки прав администратора"""
        mock_message.from_user.id = 111222333  # admin

        @admin_required
        async def test_handler(message):
            return "admin_success"

        with patch("interfaces.telegram.decorators.get_config", return_value=mock_config):
            result = await test_handler(mock_message)
            assert result == "admin_success"

    @pytest.mark.asyncio
    async def test_admin_required_unauthorized(self, mock_message, mock_config):
        """Тест неавторизованного доступа к команде администратора"""
        mock_message.from_user.id = 123456789  # user

        @admin_required
        async def test_handler(message):
            return "admin_success"

        with patch("interfaces.telegram.decorators.get_config", return_value=mock_config):
            result = await test_handler(mock_message)
            assert result is None

            mock_message.reply.assert_called_once_with("🚫 Эта команда доступна только для роли: admin")

    @pytest.mark.asyncio
    async def test_owner_required_success(self, mock_message, mock_config, mock_handler_self):
        """Тест успешной проверки прав владельца"""
        mock_message.from_user.id = 999888777  # owner

        @owner_required
        async def test_handler(self, message):
            return "owner_success"

        with patch("interfaces.telegram.decorators.get_config", return_value=mock_config):
            result = await test_handler(mock_handler_self, mock_message)
            assert result == "owner_success"

    @pytest.mark.asyncio
    async def test_owner_required_admin_unauthorized(self, mock_message, mock_config, mock_handler_self):
        """Тест что администратор не может выполнять команды владельца"""
        mock_message.from_user.id = 111222333  # admin

        @owner_required
        async def test_handler(self, message):
            return "owner_success"

        with patch("interfaces.telegram.decorators.get_config", return_value=mock_config):
            result = await test_handler(mock_handler_self, mock_message)
            assert result is None

            mock_message.reply.assert_called_once_with("🚫 Эта команда доступна только владельцу бота.")


if __name__ == "__main__":
    pytest.main([__file__])
