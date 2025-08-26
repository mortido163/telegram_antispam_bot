import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict

logger = logging.getLogger(__name__)


@dataclass
class Metrics:
    """Класс для сбора и хранения метрик приложения"""

    # Счетчики
    messages_processed: int = 0
    violations_detected: int = 0
    users_banned: int = 0
    users_unbanned: int = 0
    users_muted: int = 0
    users_kicked: int = 0
    warnings_issued: int = 0
    commands_executed: int = 0
    database_errors: int = 0

    # Временные метрики
    response_times: deque = field(default_factory=lambda: deque(maxlen=1000))
    database_query_times: deque = field(default_factory=lambda: deque(maxlen=1000))

    # Счетчики по чатам
    chat_metrics: Dict[int, Dict[str, int]] = field(default_factory=lambda: defaultdict(lambda: defaultdict(int)))

    # Время запуска
    start_time: datetime = field(default_factory=datetime.utcnow)

    def increment_messages_processed(self, chat_id: int = None):
        """Увеличить счетчик обработанных сообщений"""
        self.messages_processed += 1
        if chat_id:
            self.chat_metrics[chat_id]["messages_processed"] += 1

    def increment_violations_detected(self, chat_id: int = None):
        """Увеличить счетчик обнаруженных нарушений"""
        self.violations_detected += 1
        if chat_id:
            self.chat_metrics[chat_id]["violations_detected"] += 1

    def increment_users_banned(self, chat_id: int = None):
        """Увеличить счетчик забаненных пользователей"""
        self.users_banned += 1
        if chat_id:
            self.chat_metrics[chat_id]["users_banned"] += 1

    def increment_users_unbanned(self, chat_id: int = None):
        """Увеличить счетчик разбаненных пользователей"""
        self.users_unbanned += 1
        if chat_id:
            self.chat_metrics[chat_id]["users_unbanned"] += 1

    def increment_users_muted(self, chat_id: int = None):
        """Увеличить счетчик заглушенных пользователей"""
        self.users_muted += 1
        if chat_id:
            self.chat_metrics[chat_id]["users_muted"] += 1

    def increment_users_kicked(self, chat_id: int = None):
        """Увеличить счетчик исключенных пользователей"""
        self.users_kicked += 1
        if chat_id:
            self.chat_metrics[chat_id]["users_kicked"] += 1

    def increment_warnings_issued(self, chat_id: int = None):
        """Увеличить счетчик выданных предупреждений"""
        self.warnings_issued += 1
        if chat_id:
            self.chat_metrics[chat_id]["warnings_issued"] += 1

    def increment_commands_executed(self, command: str = None):
        """Увеличить счетчик выполненных команд"""
        self.commands_executed += 1
        if command:
            self.chat_metrics[0][f"command_{command}"] += 1

    def increment_database_errors(self):
        """Увеличить счетчик ошибок базы данных"""
        self.database_errors += 1

    def add_response_time(self, response_time: float):
        """Добавить время ответа"""
        self.response_times.append(response_time)

    def add_database_query_time(self, query_time: float):
        """Добавить время выполнения запроса к БД"""
        self.database_query_times.append(query_time)

    def get_average_response_time(self) -> float:
        """Получить среднее время ответа"""
        if not self.response_times:
            return 0.0
        return sum(self.response_times) / len(self.response_times)

    def get_average_database_query_time(self) -> float:
        """Получить среднее время выполнения запроса к БД"""
        if not self.database_query_times:
            return 0.0
        return sum(self.database_query_times) / len(self.database_query_times)

    def get_uptime(self) -> timedelta:
        """Получить время работы приложения"""
        return datetime.utcnow() - self.start_time

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Получить сводку метрик"""
        uptime = self.get_uptime()
        return {
            "uptime_seconds": uptime.total_seconds(),
            "messages_processed": self.messages_processed,
            "violations_detected": self.violations_detected,
            "users_banned": self.users_banned,
            "users_unbanned": self.users_unbanned,
            "users_muted": self.users_muted,
            "users_kicked": self.users_kicked,
            "warnings_issued": self.warnings_issued,
            "commands_executed": self.commands_executed,
            "database_errors": self.database_errors,
            "average_response_time": self.get_average_response_time(),
            "average_database_query_time": self.get_average_database_query_time(),
            "chat_count": len(self.chat_metrics),
        }

    def get_prometheus_metrics(self) -> str:
        """Получить метрики в формате Prometheus"""
        summary = self.get_metrics_summary()

        metrics = []
        for key, value in summary.items():
            if isinstance(value, (int, float)):
                metrics.append(f"telegram_bot_{key} {value}")

        return "\n".join(metrics)

    def log_metrics_summary(self):
        """Логировать сводку метрик"""
        summary = self.get_metrics_summary()
        logger.info(f"Метрики приложения: {summary}")


# Глобальный экземпляр метрик
metrics = Metrics()


def time_it(func):
    """Декоратор для измерения времени выполнения функции"""

    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            metrics.add_response_time(execution_time)
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            metrics.add_response_time(execution_time)
            logger.error(f"Ошибка в функции {func.__name__}: {e}")
            raise

    return wrapper


def database_time_it(func):
    """Декоратор для измерения времени выполнения запросов к БД"""

    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            metrics.add_database_query_time(execution_time)
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            metrics.add_database_query_time(execution_time)
            metrics.increment_database_errors()
            logger.error(f"Ошибка БД в функции {func.__name__}: {e}")
            raise

    return wrapper
