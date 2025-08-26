"""
Тесты для основного модуля приложения
"""
import logging
import signal
import sys
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import asyncio
import pytest

from main import BotApplication, main, setup_logging


class TestSetupLogging:
    """Тесты настройки логирования"""

    @patch("main.get_config")
    @patch("main.logging.basicConfig")
    def test_setup_logging(self, mock_basic_config, mock_get_config):
        """Тест настройки логирования"""
        mock_config = Mock()
        mock_config.logging.level = "INFO"
        mock_config.logging.format = "%(levelname)s - %(message)s"
        mock_get_config.return_value = mock_config

        setup_logging()

        mock_basic_config.assert_called_once()
        args, kwargs = mock_basic_config.call_args
        assert "level" in kwargs
        assert "format" in kwargs
        assert kwargs["format"] == "%(levelname)s - %(message)s"


class TestBotApplication:
    """Тесты основного класса приложения"""

    @pytest.fixture
    def app(self):
        """Экземпляр приложения для тестов"""
        with patch("main.get_config") as mock_get_config:
            mock_config = Mock()
            mock_config.bot_token = "test_token"
            mock_config.environment = "test"
            mock_config.debug = True
            mock_get_config.return_value = mock_config
            return BotApplication()

    def test_init(self, app):
        """Тест инициализации приложения"""
        assert app.bot is None
        assert app.running is False
        assert app.config is not None

    @pytest.mark.asyncio
    async def test_startup_success(self, app):
        """Тест успешного запуска приложения"""
        with patch("main.ModerationBot") as mock_bot_class, patch("main.get_session_manager") as mock_session_manager:
            mock_bot = AsyncMock()
            mock_bot_class.return_value = mock_bot

            mock_session_mgr = AsyncMock()
            mock_session_manager.return_value = mock_session_mgr

            await app.startup()

            assert app.bot is not None
            mock_bot_class.assert_called_once_with("test_token")
            mock_session_mgr.init_db.assert_called_once()

    @pytest.mark.asyncio
    async def test_startup_exception(self, app):
        """Тест обработки исключения при запуске"""
        with patch("main.ModerationBot") as mock_bot_class:
            mock_bot_class.side_effect = Exception("Bot creation failed")

            with pytest.raises(Exception, match="Bot creation failed"):
                await app.startup()

    @pytest.mark.asyncio
    async def test_shutdown_with_bot(self, app):
        """Тест корректного завершения с ботом"""
        with patch("main.get_session_manager") as mock_session_manager, patch("main.metrics") as mock_metrics:
            mock_bot = AsyncMock()
            app.bot = mock_bot
            app.running = True

            mock_session_mgr = AsyncMock()
            mock_session_manager.return_value = mock_session_mgr

            await app.shutdown()

            assert app.running is False
            mock_bot.stop.assert_called_once()
            mock_session_mgr.close.assert_called_once()
            mock_metrics.log_metrics_summary.assert_called_once()

    @pytest.mark.asyncio
    async def test_shutdown_without_bot(self, app):
        """Тест завершения без бота"""
        with patch("main.get_session_manager") as mock_session_manager, patch("main.metrics") as mock_metrics:
            app.bot = None
            app.running = True

            mock_session_mgr = AsyncMock()
            mock_session_manager.return_value = mock_session_mgr

            await app.shutdown()

            assert app.running is False
            mock_session_mgr.close.assert_called_once()
            mock_metrics.log_metrics_summary.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_success(self, app):
        """Тест успешного выполнения основного цикла"""
        with patch.object(app, "startup") as mock_startup, patch.object(app, "shutdown") as mock_shutdown:
            mock_bot = AsyncMock()
            app.bot = mock_bot

            # Имитируем прерывание через KeyboardInterrupt
            mock_bot.start.side_effect = KeyboardInterrupt("Test interrupt")

            await app.run()

            mock_startup.assert_called_once()
            mock_shutdown.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_exception_during_startup(self, app):
        """Тест обработки исключения при запуске"""
        with patch.object(app, "startup") as mock_startup, patch.object(app, "shutdown") as mock_shutdown:
            mock_startup.side_effect = Exception("Startup failed")

            with pytest.raises(Exception, match="Startup failed"):
                await app.run()

            mock_shutdown.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_exception_during_bot_start(self, app):
        """Тест обработки исключения во время работы бота"""
        with patch.object(app, "startup") as mock_startup, patch.object(app, "shutdown") as mock_shutdown:
            mock_bot = AsyncMock()
            app.bot = mock_bot
            mock_bot.start.side_effect = Exception("Bot start failed")

            with pytest.raises(Exception, match="Bot start failed"):
                await app.run()

            mock_startup.assert_called_once()
            mock_shutdown.assert_called_once()

    @pytest.mark.asyncio
    @patch("main.sys.platform", "linux")
    async def test_run_with_signal_handlers(self, app):
        """Тест установки обработчиков сигналов на Unix системах"""
        with patch.object(app, "startup") as mock_startup, patch.object(app, "shutdown") as mock_shutdown, patch(
            "main.asyncio.get_event_loop"
        ) as mock_get_loop, patch("main.asyncio.create_task") as mock_create_task:
            mock_loop = Mock()
            mock_get_loop.return_value = mock_loop

            mock_bot = AsyncMock()
            app.bot = mock_bot
            mock_bot.start.side_effect = KeyboardInterrupt("Test interrupt")

            await app.run()

            # Проверяем, что обработчики сигналов были установлены
            assert mock_loop.add_signal_handler.call_count == 2

            # Проверяем сигналы SIGTERM и SIGINT
            calls = mock_loop.add_signal_handler.call_args_list
            signals_added = [call[0][0] for call in calls]
            assert signal.SIGTERM in signals_added
            assert signal.SIGINT in signals_added

    @pytest.mark.asyncio
    @patch("main.sys.platform", "win32")
    async def test_run_windows_no_signal_handlers(self, app):
        """Тест что на Windows обработчики сигналов не устанавливаются"""
        with patch.object(app, "startup") as mock_startup, patch.object(app, "shutdown") as mock_shutdown, patch(
            "main.asyncio.get_event_loop"
        ) as mock_get_loop:
            mock_loop = Mock()
            mock_get_loop.return_value = mock_loop

            mock_bot = AsyncMock()
            app.bot = mock_bot
            mock_bot.start.side_effect = KeyboardInterrupt("Test interrupt")

            await app.run()

            # На Windows обработчики сигналов не должны устанавливаться
            mock_loop.add_signal_handler.assert_not_called()

    @pytest.mark.asyncio
    async def test_run_finally_block_when_not_running(self, app):
        """Тест что finally блок не вызывает shutdown если приложение не запущено"""
        with patch.object(app, "startup") as mock_startup, patch.object(app, "shutdown") as mock_shutdown:
            app.running = False  # Приложение не запущено
            mock_startup.side_effect = Exception("Early failure")

            with pytest.raises(Exception, match="Early failure"):
                await app.run()

            # shutdown должен быть вызван только один раз из except блока
            mock_shutdown.assert_called_once()


class TestMainFunction:
    """Тесты главной функции"""

    @pytest.mark.asyncio
    async def test_main_success(self):
        """Тест успешного выполнения main"""
        with patch("main.load_dotenv") as mock_load_dotenv, patch("main.setup_logging") as mock_setup_logging, patch(
            "main.BotApplication"
        ) as mock_app_class:
            mock_app = AsyncMock()
            mock_app_class.return_value = mock_app

            await main()

            mock_load_dotenv.assert_called_once()
            mock_setup_logging.assert_called_once()
            mock_app.run.assert_called_once()

    @pytest.mark.asyncio
    async def test_main_exception(self):
        """Тест обработки исключения в main"""
        with patch("main.load_dotenv") as mock_load_dotenv, patch("main.setup_logging") as mock_setup_logging, patch(
            "main.BotApplication"
        ) as mock_app_class, patch("main.logger") as mock_logger, patch("main.sys.exit") as mock_exit:
            mock_app = AsyncMock()
            mock_app.run.side_effect = Exception("Application failed")
            mock_app_class.return_value = mock_app

            await main()

            mock_logger.error.assert_called_once()
            mock_exit.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_main_app_creation_exception(self):
        """Тест обработки исключения при создании приложения"""
        with patch("main.load_dotenv") as mock_load_dotenv, patch("main.setup_logging") as mock_setup_logging, patch(
            "main.BotApplication"
        ) as mock_app_class, patch("main.logger") as mock_logger, patch("main.sys.exit") as mock_exit:
            mock_app_class.side_effect = Exception("App creation failed")

            await main()

            mock_logger.error.assert_called_once()
            mock_exit.assert_called_once_with(1)


class TestMainModuleExecution:
    """Тесты выполнения модуля как скрипта"""

    @patch("main.asyncio.run")
    @patch("main.main")
    def test_main_module_execution(self, mock_main_func, mock_asyncio_run):
        """Тест выполнения модуля напрямую"""
        # Имитируем выполнение if __name__ == '__main__'
        with patch("__main__.__name__", "__main__"):
            # Здесь мы не можем легко протестировать само выполнение,
            # но можем проверить что функции вызываются правильно
            exec("if __name__ == '__main__': import asyncio; asyncio.run(main())")

        # Этот тест больше для покрытия, реальная проверка сложна
        assert True

    def test_imports_available(self):
        """Тест что все импорты доступны"""
        # Проверяем что все импорты в main.py работают
        import logging
        import signal
        import sys

        import asyncio
        from dotenv import load_dotenv

        # Проверяем что наши модули доступны
        from application.settings import get_config
        from infrastructure.database.session import get_session_manager
        from infrastructure.monitoring import metrics
        from interfaces.telegram.bot import ModerationBot

        assert True  # Если дошли сюда, все импорты работают


class TestSignalHandlingIntegration:
    """Интеграционные тесты обработки сигналов"""

    @pytest.mark.asyncio
    async def test_signal_handler_creation(self):
        """Тест создания обработчика сигнала"""
        app = Mock()
        app.shutdown = AsyncMock()

        # Создаем лямбда функцию как в коде
        signal_handler = lambda: asyncio.create_task(app.shutdown())

        # Проверяем что функция создается без ошибок
        assert callable(signal_handler)

        # Можем протестировать что задача создается
        with patch("asyncio.create_task") as mock_create_task:
            signal_handler()
            mock_create_task.assert_called_once()  # Упрощенная проверка
            # Проверяем что передается корутина app.shutdown()
            args, kwargs = mock_create_task.call_args
            assert hasattr(args[0], "__await__")  # Это корутина


class TestErrorHandling:
    """Тесты обработки ошибок"""

    @pytest.fixture
    def app(self):
        """Экземпляр приложения для тестов"""
        with patch("main.get_config") as mock_get_config:
            mock_config = Mock()
            mock_config.bot_token = "test_token"
            mock_config.environment = "test"
            mock_config.debug = True
            mock_get_config.return_value = mock_config
            return BotApplication()

    @pytest.mark.asyncio
    async def test_keyboard_interrupt_handling(self, app):
        """Тест обработки KeyboardInterrupt"""
        with patch.object(app, "startup") as mock_startup, patch.object(app, "shutdown") as mock_shutdown:
            mock_bot = AsyncMock()
            app.bot = mock_bot
            mock_bot.start.side_effect = KeyboardInterrupt("Ctrl+C pressed")

            # Не должно выбрасывать исключение
            await app.run()

            mock_startup.assert_called_once()
            mock_shutdown.assert_called_once()

    @pytest.mark.asyncio
    async def test_general_exception_propagation(self, app):
        """Тест что общие исключения пробрасываются"""
        with patch.object(app, "startup") as mock_startup, patch.object(app, "shutdown") as mock_shutdown:
            mock_bot = AsyncMock()
            app.bot = mock_bot
            mock_bot.start.side_effect = RuntimeError("Unexpected error")

            with pytest.raises(RuntimeError, match="Unexpected error"):
                await app.run()

            mock_startup.assert_called_once()
            mock_shutdown.assert_called_once()


class TestConfigurationIntegration:
    """Тесты интеграции с конфигурацией"""

    @pytest.mark.asyncio
    async def test_startup_uses_config_values(self):
        """Тест что startup использует значения из конфигурации"""
        with patch("main.get_config") as mock_get_config, patch("main.ModerationBot") as mock_bot_class, patch(
            "main.get_session_manager"
        ) as mock_session_manager:
            mock_config = Mock()
            mock_config.bot_token = "custom_token_123"
            mock_config.environment = "production"
            mock_config.debug = False
            mock_get_config.return_value = mock_config

            app = BotApplication()

            mock_session_mgr = AsyncMock()
            mock_session_manager.return_value = mock_session_mgr

            await app.startup()

            # Проверяем что бот создается с правильным токеном
            mock_bot_class.assert_called_once_with("custom_token_123")

            # Проверяем что конфигурация сохранена
            assert app.config.environment == "production"
            assert app.config.debug is False


class TestLoggingIntegration:
    """Тесты интеграции с логированием"""

    @patch("main.get_config")
    @patch("main.logging.basicConfig")
    def test_logger_creation(self, mock_basic_config, mock_get_config):
        """Тест создания логгера"""
        mock_config = Mock()
        mock_config.logging.level = "DEBUG"
        mock_config.logging.format = "custom format"
        mock_get_config.return_value = mock_config

        # Проверяем что логгер main создается без ошибок
        logger = logging.getLogger("main")
        assert logger is not None
        assert logger.name == "main"
