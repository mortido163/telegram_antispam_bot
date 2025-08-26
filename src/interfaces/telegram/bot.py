import logging
from typing import Optional

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message

from application.enhanced_config import EnhancedModerationConfig
from application.services.moderation_service import TelegramModerationService
from infrastructure.database.session import get_session_manager
from infrastructure.monitoring import metrics, time_it
from infrastructure.repositories import SQLAlchemyMessageRepository, SQLAlchemyUserRepository

from .handlers import ModeratorCommandHandlers

logger = logging.getLogger(__name__)


class ModerationBot:
    def __init__(self, token: str):
        # Инициализация бота и диспетчера
        self.bot = Bot(token=token, parse_mode=ParseMode.HTML)
        self.dp = Dispatcher()

        # Инициализация репозиториев
        self.user_repository = SQLAlchemyUserRepository()
        self.message_repository = SQLAlchemyMessageRepository()

        # Инициализация улучшенной конфигурации
        self.config = EnhancedModerationConfig()

        # Инициализация сервисов
        self.moderation_service = TelegramModerationService(
            user_repository=self.user_repository, message_repository=self.message_repository, config=self.config
        )

        # Инициализация обработчиков
        self.command_handlers = ModeratorCommandHandlers(
            moderation_service=self.moderation_service, user_repository=self.user_repository
        )

        self._register_handlers()
        logger.info("Модерационный бот инициализирован")

    def _register_handlers(self):
        """Регистрация всех обработчиков"""
        # Регистрация обработчиков сообщений
        self.dp.message.register(self.command_handlers.handle_message)

        # Регистрация обработчиков команд модерации
        self.dp.message.register(self.command_handlers.ban_command, Command("ban"))
        self.dp.message.register(self.command_handlers.unban_command, Command("unban"))
        self.dp.message.register(self.command_handlers.mute_command, Command("mute"))
        self.dp.message.register(self.command_handlers.unmute_command, Command("unmute"))
        self.dp.message.register(self.command_handlers.kick_command, Command("kick"))
        self.dp.message.register(self.command_handlers.set_warnings_limit_command, Command("set_warnings"))

        # Регистрация команд управления запрещенными словами
        self.dp.message.register(self.command_handlers.add_forbidden_word_command, Command("add_forbidden"))
        self.dp.message.register(self.command_handlers.remove_forbidden_word_command, Command("remove_forbidden"))
        self.dp.message.register(self.command_handlers.list_forbidden_words_command, Command("list_forbidden"))
        self.dp.message.register(self.command_handlers.clear_forbidden_words_command, Command("clear_forbidden"))

        # Дополнительные команды
        self.dp.message.register(self.command_handlers.bot_status_command, Command("bot_status"))
        self.dp.message.register(self.command_handlers.help_command, Command("help", "start"))
        self.dp.message.register(self.stats_command, Command("stats"))

    async def start(self):
        """Запустить бота"""
        logger.info("Инициализация базы данных...")
        # Инициализация базы данных
        session_manager = get_session_manager()
        await session_manager.init_db()

        logger.info("Запуск polling бота...")
        await self.dp.start_polling(self.bot)

    async def stop(self):
        """Остановить бота"""
        logger.info("Остановка бота...")
        await self.dp.stop_polling()
        await self.bot.session.close()

    @time_it
    async def stats_command(self, message: Message) -> None:
        """Показать статистику бота"""
        metrics.increment_commands_executed("stats")

        try:
            summary = metrics.get_metrics_summary()
            uptime_hours = summary["uptime_seconds"] / 3600

            stats_text = f"""📊 **Статистика бота**

🕐 Время работы: {uptime_hours:.1f} часов
📨 Обработано сообщений: {summary['messages_processed']}
⚠️ Обнаружено нарушений: {summary['violations_detected']}
🚫 Пользователей забанено: {summary['users_banned']}
🔇 Пользователей заглушено: {summary['users_muted']}
👢 Пользователей исключено: {summary['users_kicked']}
⚡ Выдано предупреждений: {summary['warnings_issued']}
🤖 Выполнено команд: {summary['commands_executed']}
⏱️ Среднее время ответа: {summary['average_response_time']:.3f}с
💾 Ошибок БД: {summary['database_errors']}
💬 Активных чатов: {summary['chat_count']}"""

            await message.reply(stats_text)
        except Exception as e:
            await message.reply(f"❌ Ошибка при получении статистики: {str(e)}")
            logger.error(f"Ошибка при получении статистики: {e}")
