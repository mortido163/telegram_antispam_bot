from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest

from interfaces.telegram.bot import ModerationBot


@pytest.fixture
def mock_bot():
    """Mock объект Bot для aiogram"""
    bot = Mock()
    bot.session = Mock()
    bot.session.close = AsyncMock()
    bot.ban_chat_member = AsyncMock()
    bot.unban_chat_member = AsyncMock()
    bot.restrict_chat_member = AsyncMock()
    return bot


@pytest.fixture
def mock_dispatcher():
    """Mock объект Dispatcher для aiogram"""
    dp = Mock()
    dp.message = Mock()
    dp.message.register = Mock()
    dp.start_polling = AsyncMock()
    dp.stop_polling = AsyncMock()
    return dp


class TestModerationBotInitialization:
    def test_bot_initialization_with_token(self):
        """Тест инициализации бота с токеном"""
        with patch("interfaces.telegram.bot.Bot") as mock_bot_class, patch(
            "interfaces.telegram.bot.Dispatcher"
        ) as mock_dispatcher_class, patch("interfaces.telegram.bot.SQLAlchemyUserRepository"), patch(
            "interfaces.telegram.bot.SQLAlchemyMessageRepository"
        ), patch(
            "interfaces.telegram.bot.EnhancedModerationConfig"
        ), patch(
            "interfaces.telegram.bot.TelegramModerationService"
        ), patch(
            "interfaces.telegram.bot.ModeratorCommandHandlers"
        ):
            bot = ModerationBot("test_token")

            mock_bot_class.assert_called_once()
            mock_dispatcher_class.assert_called_once()

    def test_bot_initialization_components(self):
        """Тест инициализации компонентов бота"""
        with patch("interfaces.telegram.bot.Bot"), patch("interfaces.telegram.bot.Dispatcher"), patch(
            "interfaces.telegram.bot.SQLAlchemyUserRepository"
        ), patch("interfaces.telegram.bot.SQLAlchemyMessageRepository"), patch(
            "interfaces.telegram.bot.EnhancedModerationConfig"
        ), patch(
            "interfaces.telegram.bot.TelegramModerationService"
        ), patch(
            "interfaces.telegram.bot.ModeratorCommandHandlers"
        ):
            bot = ModerationBot("test_token")

            assert hasattr(bot, "bot")
            assert hasattr(bot, "dp")
            assert hasattr(bot, "user_repository")
            assert hasattr(bot, "message_repository")
            assert hasattr(bot, "config")
            assert hasattr(bot, "moderation_service")
            assert hasattr(bot, "command_handlers")


class TestModerationBotHandlerRegistration:
    def test_handlers_registration(self, mock_dispatcher):
        """Тест регистрации обработчиков"""
        with patch("interfaces.telegram.bot.Bot"), patch(
            "interfaces.telegram.bot.Dispatcher", return_value=mock_dispatcher
        ), patch("interfaces.telegram.bot.SQLAlchemyUserRepository"), patch(
            "interfaces.telegram.bot.SQLAlchemyMessageRepository"
        ), patch(
            "interfaces.telegram.bot.EnhancedModerationConfig"
        ), patch(
            "interfaces.telegram.bot.TelegramModerationService"
        ), patch(
            "interfaces.telegram.bot.ModeratorCommandHandlers"
        ):
            bot = ModerationBot("test_token")

            # Проверяем что register был вызван для сообщений
            assert mock_dispatcher.message.register.call_count > 0


class TestModerationBotStartStop:
    @pytest.mark.asyncio
    async def test_start_bot_success(self, mock_bot, mock_dispatcher):
        """Тест успешного запуска бота"""
        with patch("interfaces.telegram.bot.Bot", return_value=mock_bot), patch(
            "interfaces.telegram.bot.Dispatcher", return_value=mock_dispatcher
        ), patch("interfaces.telegram.bot.SQLAlchemyUserRepository"), patch(
            "interfaces.telegram.bot.SQLAlchemyMessageRepository"
        ), patch(
            "interfaces.telegram.bot.EnhancedModerationConfig"
        ), patch(
            "interfaces.telegram.bot.TelegramModerationService"
        ), patch(
            "interfaces.telegram.bot.ModeratorCommandHandlers"
        ), patch(
            "interfaces.telegram.bot.get_session_manager"
        ) as mock_session_manager:
            mock_session_manager.return_value.init_db = AsyncMock()

            bot = ModerationBot("test_token")
            await bot.start()

            mock_session_manager.return_value.init_db.assert_awaited_once()
            mock_dispatcher.start_polling.assert_awaited_once_with(mock_bot)

    @pytest.mark.asyncio
    async def test_stop_bot_success(self, mock_bot, mock_dispatcher):
        """Тест успешной остановки бота"""
        with patch("interfaces.telegram.bot.Bot", return_value=mock_bot), patch(
            "interfaces.telegram.bot.Dispatcher", return_value=mock_dispatcher
        ), patch("interfaces.telegram.bot.SQLAlchemyUserRepository"), patch(
            "interfaces.telegram.bot.SQLAlchemyMessageRepository"
        ), patch(
            "interfaces.telegram.bot.EnhancedModerationConfig"
        ), patch(
            "interfaces.telegram.bot.TelegramModerationService"
        ), patch(
            "interfaces.telegram.bot.ModeratorCommandHandlers"
        ):
            bot = ModerationBot("test_token")
            await bot.stop()

            mock_dispatcher.stop_polling.assert_awaited_once()
            mock_bot.session.close.assert_awaited_once()


class TestModerationBotStatsCommand:
    @pytest.mark.asyncio
    async def test_stats_command_success(self, mock_bot, mock_dispatcher):
        """Тест команды статистики"""
        mock_message = Mock()
        mock_message.reply = AsyncMock()

        with patch("interfaces.telegram.bot.Bot", return_value=mock_bot), patch(
            "interfaces.telegram.bot.Dispatcher", return_value=mock_dispatcher
        ), patch("interfaces.telegram.bot.SQLAlchemyUserRepository"), patch(
            "interfaces.telegram.bot.SQLAlchemyMessageRepository"
        ), patch(
            "interfaces.telegram.bot.EnhancedModerationConfig"
        ), patch(
            "interfaces.telegram.bot.TelegramModerationService"
        ), patch(
            "interfaces.telegram.bot.ModeratorCommandHandlers"
        ), patch(
            "interfaces.telegram.bot.metrics"
        ) as mock_metrics:
            mock_metrics.get_metrics_summary.return_value = {
                "uptime_seconds": 3600,
                "messages_processed": 100,
                "violations_detected": 5,
                "users_banned": 2,
                "users_muted": 1,
                "users_kicked": 1,
                "warnings_issued": 10,
                "commands_executed": 20,
                "average_response_time": 0.05,
                "database_errors": 0,
                "chat_count": 5,
            }

            bot = ModerationBot("test_token")
            await bot.stats_command(mock_message)

            mock_message.reply.assert_awaited_once()
            args = mock_message.reply.call_args[0][0]
            assert "100" in args  # messages_processed
            assert "1.0" in args  # uptime hours

    @pytest.mark.asyncio
    async def test_stats_command_exception_handling(self, mock_bot, mock_dispatcher):
        """Тест обработки исключений в команде статистики"""
        mock_message = Mock()
        mock_message.reply = AsyncMock()

        with patch("interfaces.telegram.bot.Bot", return_value=mock_bot), patch(
            "interfaces.telegram.bot.Dispatcher", return_value=mock_dispatcher
        ), patch("interfaces.telegram.bot.SQLAlchemyUserRepository"), patch(
            "interfaces.telegram.bot.SQLAlchemyMessageRepository"
        ), patch(
            "interfaces.telegram.bot.EnhancedModerationConfig"
        ), patch(
            "interfaces.telegram.bot.TelegramModerationService"
        ), patch(
            "interfaces.telegram.bot.ModeratorCommandHandlers"
        ), patch(
            "interfaces.telegram.bot.metrics"
        ) as mock_metrics, patch(
            "interfaces.telegram.bot.logger"
        ) as mock_logger:
            mock_metrics.get_metrics_summary.side_effect = Exception("Metrics error")

            bot = ModerationBot("test_token")
            await bot.stats_command(mock_message)

            mock_message.reply.assert_awaited_once()
            args = mock_message.reply.call_args[0][0]
            assert "Ошибка" in args
            mock_logger.error.assert_called_once()


class TestModerationBotIntegration:
    def test_service_dependencies(self):
        """Тест зависимостей сервисов"""
        with patch("interfaces.telegram.bot.Bot"), patch("interfaces.telegram.bot.Dispatcher"), patch(
            "interfaces.telegram.bot.SQLAlchemyUserRepository"
        ) as mock_user_repo, patch("interfaces.telegram.bot.SQLAlchemyMessageRepository") as mock_msg_repo, patch(
            "interfaces.telegram.bot.EnhancedModerationConfig"
        ) as mock_config, patch(
            "interfaces.telegram.bot.TelegramModerationService"
        ) as mock_service, patch(
            "interfaces.telegram.bot.ModeratorCommandHandlers"
        ) as mock_handlers:
            bot = ModerationBot("test_token")

            # Проверяем что сервисы созданы с правильными зависимостями
            mock_user_repo.assert_called_once()
            mock_msg_repo.assert_called_once()
            mock_config.assert_called_once()
            mock_service.assert_called_once()
            mock_handlers.assert_called_once()

    def test_command_handlers_initialization(self):
        """Тест инициализации обработчиков команд"""
        with patch("interfaces.telegram.bot.Bot"), patch("interfaces.telegram.bot.Dispatcher"), patch(
            "interfaces.telegram.bot.SQLAlchemyUserRepository"
        ), patch("interfaces.telegram.bot.SQLAlchemyMessageRepository"), patch(
            "interfaces.telegram.bot.EnhancedModerationConfig"
        ), patch(
            "interfaces.telegram.bot.TelegramModerationService"
        ) as mock_service, patch(
            "interfaces.telegram.bot.ModeratorCommandHandlers"
        ) as mock_handlers:
            bot = ModerationBot("test_token")

            # Проверяем что обработчики созданы с правильными зависимостями
            call_args = mock_handlers.call_args
            assert "moderation_service" in call_args.kwargs
            assert "user_repository" in call_args.kwargs


class TestModerationBotLifecycle:
    @pytest.mark.asyncio
    async def test_full_lifecycle(self, mock_bot, mock_dispatcher):
        """Тест полного жизненного цикла бота"""
        with patch("interfaces.telegram.bot.Bot", return_value=mock_bot), patch(
            "interfaces.telegram.bot.Dispatcher", return_value=mock_dispatcher
        ), patch("interfaces.telegram.bot.SQLAlchemyUserRepository"), patch(
            "interfaces.telegram.bot.SQLAlchemyMessageRepository"
        ), patch(
            "interfaces.telegram.bot.EnhancedModerationConfig"
        ), patch(
            "interfaces.telegram.bot.TelegramModerationService"
        ), patch(
            "interfaces.telegram.bot.ModeratorCommandHandlers"
        ), patch(
            "interfaces.telegram.bot.get_session_manager"
        ) as mock_session_manager:
            mock_session_manager.return_value.init_db = AsyncMock()

            # Создание бота
            bot = ModerationBot("test_token")

            # Запуск бота
            await bot.start()
            mock_dispatcher.start_polling.assert_awaited_once_with(mock_bot)

            # Остановка бота
            await bot.stop()
            mock_dispatcher.stop_polling.assert_awaited_once()
            mock_bot.session.close.assert_awaited_once()


class TestModerationBotConfiguration:
    def test_parse_mode_configuration(self, mock_bot):
        """Тест конфигурации режима парсинга"""
        with patch("interfaces.telegram.bot.Bot", return_value=mock_bot) as mock_bot_class, patch(
            "interfaces.telegram.bot.Dispatcher"
        ), patch("interfaces.telegram.bot.SQLAlchemyUserRepository"), patch(
            "interfaces.telegram.bot.SQLAlchemyMessageRepository"
        ), patch(
            "interfaces.telegram.bot.EnhancedModerationConfig"
        ), patch(
            "interfaces.telegram.bot.TelegramModerationService"
        ), patch(
            "interfaces.telegram.bot.ModeratorCommandHandlers"
        ):
            bot = ModerationBot("test_token")

            # Проверяем что Bot создан с правильными параметрами
            call_args = mock_bot_class.call_args
            assert call_args[1]["token"] == "test_token"
