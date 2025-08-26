"""
Декораторы для авторизации команд Telegram бота
"""
from functools import wraps
from typing import Callable, List, Union

from aiogram.types import Message as TelegramMessage

from application.settings import get_config


def owner_only(func: Callable) -> Callable:
    """
    Декоратор для команд, доступных только владельцу бота
    """

    @wraps(func)
    async def wrapper(self, message: TelegramMessage, *args, **kwargs):
        user_id = message.from_user.id
        config = get_config()

        if user_id != config.auth.owner_id:
            await message.reply("🚫 Эта команда доступна только владельцу бота.")
            return

        return await func(self, message, *args, **kwargs)

    return wrapper


def admin_only(func: Callable) -> Callable:
    """
    Декоратор для команд, доступных только администраторам
    """

    @wraps(func)
    async def wrapper(self, message: TelegramMessage, *args, **kwargs):
        user_id = message.from_user.id
        config = get_config()

        # Владелец имеет все права администратора
        if user_id == config.auth.owner_id:
            return await func(self, message, *args, **kwargs)

        # Проверяем, является ли пользователь администратором
        if user_id not in config.auth.admin_ids:
            await message.reply("🚫 Эта команда доступна только администраторам бота.")
            return

        return await func(self, message, *args, **kwargs)

    return wrapper


def chat_admin_only(func: Callable) -> Callable:
    """
    Декоратор для команд, доступных администраторам чата, администраторам бота и владельцу
    """

    @wraps(func)
    async def wrapper(self, message: TelegramMessage, *args, **kwargs):
        user_id = message.from_user.id
        config = get_config()

        # Владелец бота всегда имеет доступ
        if user_id == config.auth.owner_id:
            return await func(self, message, *args, **kwargs)

        # Администраторы бота также имеют доступ
        if user_id in config.auth.admin_ids:
            return await func(self, message, *args, **kwargs)

        # Проверяем права в чате
        try:
            chat_member = await message.bot.get_chat_member(chat_id=message.chat.id, user_id=user_id)

            if chat_member.status in ["administrator", "creator"]:
                return await func(self, message, *args, **kwargs)
            else:
                await message.reply("🚫 Эта команда доступна только администраторам чата.")
                return

        except Exception as e:
            await message.reply("❌ Не удалось проверить права доступа в чате.")
            return

    return wrapper


async def is_user_authorized(user_id: int, required_level: str = "admin", chat_id: int = None, bot=None) -> bool:
    """
    Проверить авторизацию пользователя

    Args:
        user_id: ID пользователя
        required_level: Требуемый уровень доступа ('owner', 'admin', 'chat_admin')
        chat_id: ID чата (для проверки прав администратора чата)
        bot: Экземпляр бота (для проверки прав в чате)

    Returns:
        True если пользователь авторизован, False в противном случае
    """
    config = get_config()

    # Владелец всегда имеет доступ
    if user_id == config.auth.owner_id:
        return True

    if required_level == "owner":
        return False

    # Проверяем администраторов бота
    if user_id in config.auth.admin_ids:
        return True

    if required_level == "admin":
        return False

    # Для chat_admin проверяем права в чате
    if required_level == "chat_admin" and chat_id and bot:
        try:
            chat_member = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
            return chat_member.status in ["administrator", "creator"]
        except Exception:
            return False

    return False


def get_user_role(user_id: int) -> str:
    """
    Получить роль пользователя

    Args:
        user_id: ID пользователя

    Returns:
        Роль пользователя: 'owner', 'admin', 'user'
    """
    config = get_config()

    if user_id == config.auth.owner_id:
        return "owner"
    elif user_id in config.auth.admin_ids:
        return "admin"
    else:
        return "user"


def require_role(required_role: str, unauthorized_message: str = None) -> Callable:
    """
    Декоратор для проверки роли пользователя

    Args:
        required_role: Требуемая роль ('owner', 'admin', 'user')
        unauthorized_message: Кастомное сообщение об ошибке
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(message: TelegramMessage, *args, **kwargs):
            user_id = message.from_user.id
            user_role = get_user_role(user_id)

            # Владелец имеет все роли
            if user_role == "owner":
                return await func(message, *args, **kwargs)

            # Проверяем соответствие роли
            if required_role == "admin" and user_role in ["admin"]:
                return await func(message, *args, **kwargs)
            elif required_role == "user":
                return await func(message, *args, **kwargs)

            # Отказ в доступе
            error_msg = unauthorized_message or f"🚫 Эта команда доступна только для роли: {required_role}"
            await message.reply(error_msg)
            return

        return wrapper

    return decorator


def admin_required(func: Callable) -> Callable:
    """Декоратор для команд, доступных только администраторам (включая владельца)"""
    return require_role("admin")(func)


def owner_required(func: Callable) -> Callable:
    """Декоратор для команд, доступных только владельцу"""
    return owner_only(func)
