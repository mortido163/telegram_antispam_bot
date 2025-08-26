import logging
import signal
import sys

import asyncio
from dotenv import load_dotenv

from application.settings import get_config
from infrastructure.database.session import get_session_manager
from infrastructure.monitoring import metrics
from interfaces.telegram.bot import ModerationBot


def setup_logging():
    """Настройка логирования"""
    config = get_config()
    logging.basicConfig(level=getattr(logging, config.logging.level.upper()), format=config.logging.format)


logger = logging.getLogger(__name__)


class BotApplication:
    """Основное приложение бота с поддержкой graceful shutdown"""

    def __init__(self):
        self.bot = None
        self.running = False
        self.config = get_config()

    async def startup(self):
        """Инициализация приложения"""
        logger.info("Запуск Telegram Антиспам Бота...")
        logger.info(f"Среда выполнения: {self.config.environment}")
        logger.info(f"Режим отладки: {self.config.debug}")

        # Создание экземпляра бота
        self.bot = ModerationBot(self.config.bot_token)

        # Инициализация базы данных
        logger.info("Инициализация базы данных...")
        session_manager = get_session_manager()
        await session_manager.init_db()

        logger.info("Приложение успешно инициализировано")

    async def shutdown(self):
        """Корректное завершение работы приложения"""
        logger.info("Начинаем завершение работы приложения...")
        self.running = False

        if self.bot:
            await self.bot.stop()

        # Закрытие соединений с базой данных
        session_manager = get_session_manager()
        await session_manager.close()

        # Логирование финальных метрик
        metrics.log_metrics_summary()

        logger.info("Приложение корректно завершено")

    async def run(self):
        """Запуск основного цикла приложения"""
        shutdown_called = False
        try:
            await self.startup()
            self.running = True

            # Настройка обработчиков сигналов для graceful shutdown
            if sys.platform != "win32":
                loop = asyncio.get_event_loop()
                for sig in (signal.SIGTERM, signal.SIGINT):
                    loop.add_signal_handler(sig, lambda: asyncio.create_task(self.shutdown()))

            logger.info("Бот запущен и готов к работе")
            await self.bot.start()

        except KeyboardInterrupt:
            logger.info("Получен сигнал прерывания")
        except Exception as e:
            logger.error(f"Критическая ошибка при запуске бота: {e}")
            await self.shutdown()
            shutdown_called = True
            raise
        finally:
            if self.running and not shutdown_called:
                await self.shutdown()


async def main():
    # Загрузка переменных окружения
    load_dotenv()

    # Настройка логирования
    setup_logging()

    try:
        app = BotApplication()
        await app.run()
    except Exception as e:
        logger.error(f"Ошибка при запуске приложения: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
