"""
Тесты для основного Telegram бота
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch

from interfaces.telegram.bot import ModerationBot


class TestModerationBot:
    """Тесты основного Telegram бота"""
    
    @pytest.fixture
    def telegram_bot(self):
        """Экземпляр Telegram бота"""
        with patch('interfaces.telegram.bot.Bot') as mock_bot_class, \
             patch('interfaces.telegram.bot.Dispatcher') as mock_dp_class:
            
            mock_bot = Mock()
            mock_bot.session = Mock()
            mock_bot.session.close = AsyncMock()
            mock_bot_class.return_value = mock_bot
            
            mock_dp = Mock()
            mock_dp.stop_polling = AsyncMock()
            mock_dp.message = Mock()
            mock_dp.message.handlers = []
            mock_dp.message.register = Mock()
            mock_dp_class.return_value = mock_dp
            
            bot = ModerationBot("test_token")
            return bot
    
    def test_init(self):
        """Тест инициализации бота"""
        with patch('interfaces.telegram.bot.Bot') as mock_bot_class, \
             patch('interfaces.telegram.bot.Dispatcher') as mock_dp_class:
            
            mock_bot_instance = Mock()
            mock_dp_instance = Mock()
            mock_bot_class.return_value = mock_bot_instance
            mock_dp_class.return_value = mock_dp_instance
            
            bot = ModerationBot("test_token")
            
            # Проверяем создание экземпляров
            mock_bot_class.assert_called_once()
            mock_dp_class.assert_called_once()  # Без аргументов в новых версиях aiogram
            
            assert bot.bot == mock_bot_instance
            assert bot.dp == mock_dp_instance
    
    def test_setup_handlers(self, telegram_bot):
        """Тест настройки обработчиков"""
        # Симулируем добавление обработчиков при вызове register
        def mock_register(*args, **kwargs):
            telegram_bot.dp.message.handlers.append(args[0])
        
        telegram_bot.dp.message.register.side_effect = mock_register
        
        telegram_bot._register_handlers()
        
        # Проверяем, что регистрируются обработчики
        dp = telegram_bot.dp
        
        # Проверяем регистрацию обработчиков сообщений
        # В новой версии aiogram используется dp.message.register
        assert hasattr(dp, 'message')
        assert hasattr(dp.message, 'register')
        
        # Проверяем что обработчики зарегистрированы
        # Это можно проверить через количество зарегистрированных обработчиков
        assert len(dp.message.handlers) > 0


if __name__ == "__main__":
    pytest.main([__file__])
