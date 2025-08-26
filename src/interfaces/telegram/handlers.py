from datetime import datetime
from typing import List, Optional

from aiogram import types
from aiogram.types import Message as TelegramMessage

from application.services.moderation_service import TelegramModerationService
from domain.entities.message import Message
from domain.entities.user import User
from domain.exceptions import UserAlreadyBannedError, UserAlreadyMutedError, UserNotBannedError, UserNotMutedError
from domain.interfaces.repositories import UserRepository

from .decorators import admin_only, chat_admin_only, owner_only


class ModeratorCommandHandlers:
    def __init__(self, moderation_service: TelegramModerationService, user_repository: UserRepository):
        self.moderation_service = moderation_service
        self.user_repository = user_repository

    async def handle_message(self, message: TelegramMessage) -> None:
        """Обработать обычное сообщение чата"""
        if message.text:
            domain_message = Message(
                message_id=message.message_id,
                user_id=message.from_user.id,
                chat_id=message.chat.id,
                text=message.text,
                timestamp=datetime.utcnow(),
            )

            violations = await self.moderation_service.check_message(domain_message)
            if violations:
                await message.reply(
                    f"⚠️ Сообщение содержит запрещенные слова: {', '.join(violations)}\n" f"Сообщение записано как нарушение."
                )

    @chat_admin_only
    async def ban_command(self, message: TelegramMessage) -> None:
        """Забанить пользователя в чате"""
        if not message.reply_to_message:
            await message.reply("Эта команда должна использоваться как ответ на сообщение")
            return

        target_user = await self._get_target_user(message)
        if not target_user:
            return

        try:
            await self.moderation_service.ban_user(target_user)
            await message.bot.ban_chat_member(chat_id=message.chat.id, user_id=target_user.user_id)
            await message.reply(f"Пользователь забанен")
        except UserAlreadyBannedError:
            await message.reply("Этот пользователь уже забанен")

    @chat_admin_only
    async def unban_command(self, message: TelegramMessage) -> None:
        """Разбанить пользователя в чате"""
        if not message.reply_to_message:
            await message.reply("Эта команда должна использоваться как ответ на сообщение")
            return

        target_user = await self._get_target_user(message)
        if not target_user:
            return

        try:
            await self.moderation_service.unban_user(target_user)
            await message.bot.unban_chat_member(chat_id=message.chat.id, user_id=target_user.user_id, only_if_banned=True)
            await message.reply(f"Пользователь разбанен")
        except UserNotBannedError:
            await message.reply("Этот пользователь не забанен")

    @chat_admin_only
    async def mute_command(self, message: TelegramMessage) -> None:
        """Ограничить пользователя в отправке сообщений"""
        if not message.reply_to_message:
            await message.reply("Эта команда должна использоваться как ответ на сообщение")
            return

        target_user = await self._get_target_user(message)
        if not target_user:
            return

        try:
            await self.moderation_service.mute_user(target_user)
            await message.bot.restrict_chat_member(
                chat_id=message.chat.id,
                user_id=target_user.user_id,
                permissions=types.ChatPermissions(can_send_messages=False),
            )
            await message.reply(f"Пользователь заглушен")
        except UserAlreadyMutedError:
            await message.reply("Этот пользователь уже заглушен")

    @chat_admin_only
    async def unmute_command(self, message: TelegramMessage) -> None:
        """Разрешить пользователю отправлять сообщения"""
        if not message.reply_to_message:
            await message.reply("Эта команда должна использоваться как ответ на сообщение")
            return

        target_user = await self._get_target_user(message)
        if not target_user:
            return

        try:
            await self.moderation_service.unmute_user(target_user)
            await message.bot.restrict_chat_member(
                chat_id=message.chat.id, user_id=target_user.user_id, permissions=types.ChatPermissions(can_send_messages=True)
            )
            await message.reply(f"С пользователя снято заглушение")
        except UserNotMutedError:
            await message.reply("Этот пользователь не заглушен")

    @chat_admin_only
    async def kick_command(self, message: TelegramMessage) -> None:
        """Удалить пользователя из чата"""
        if not message.reply_to_message:
            await message.reply("Эта команда должна использоваться как ответ на сообщение")
            return

        target_user = await self._get_target_user(message)
        if not target_user:
            return

        await self.moderation_service.kick_user(target_user)
        await message.bot.ban_chat_member(chat_id=message.chat.id, user_id=target_user.user_id)
        await message.bot.unban_chat_member(chat_id=message.chat.id, user_id=target_user.user_id)
        await message.reply(f"Пользователь исключен из чата")

    @admin_only
    async def set_warnings_limit_command(self, message: TelegramMessage) -> None:
        """Установить лимит предупреждений для чата"""
        args = message.text.split()
        if len(args) != 2 or not args[1].isdigit():
            await message.reply("Пожалуйста, укажите лимит предупреждений в виде числа\n" "Использование: /set_warnings 3")
            return

        limit = int(args[1])
        if limit < 1:
            await message.reply("Лимит предупреждений должен быть положительным")
            return

        await self.moderation_service.set_warnings_limit(message.chat.id, limit)
        await message.reply(f"Лимит предупреждений установлен: {limit}")

    @admin_only
    async def add_forbidden_word_command(self, message: TelegramMessage) -> None:
        """Добавить запрещенное слово"""
        args = message.text.split(maxsplit=1)
        if len(args) != 2:
            await message.reply(
                "Пожалуйста, укажите слово для добавления в список запрещенных\n" "Использование: /add_forbidden слово"
            )
            return

        word = args[1].strip()
        if not word:
            await message.reply("Слово не может быть пустым")
            return

        await self.moderation_service.add_forbidden_word(word)
        await message.reply(f"Слово '{word}' добавлено в список запрещенных")

    @admin_only
    async def remove_forbidden_word_command(self, message: TelegramMessage) -> None:
        """Удалить запрещенное слово"""
        args = message.text.split(maxsplit=1)
        if len(args) != 2:
            await message.reply(
                "Пожалуйста, укажите слово для удаления из списка запрещенных\n" "Использование: /remove_forbidden слово"
            )
            return

        word = args[1].strip()
        if not word:
            await message.reply("Слово не может быть пустым")
            return

        success = await self.moderation_service.remove_forbidden_word(word)
        if success:
            await message.reply(f"Слово '{word}' удалено из списка запрещенных")
        else:
            await message.reply(f"Слово '{word}' не найдено в списке запрещенных")

    @admin_only
    async def list_forbidden_words_command(self, message: TelegramMessage) -> None:
        """Показать список запрещенных слов"""
        words = await self.moderation_service.get_forbidden_words()
        if not words:
            await message.reply("Список запрещенных слов пуст")
            return

        words_text = "\n".join([f"• {word}" for word in words])
        await message.reply(f"📝 Запрещенные слова:\n{words_text}")

    @owner_only
    async def clear_forbidden_words_command(self, message: TelegramMessage) -> None:
        """Очистить весь список запрещенных слов (только для владельца)"""
        await self.moderation_service.clear_forbidden_words()
        await message.reply("🗑️ Список запрещенных слов очищен")

    @admin_only
    async def bot_status_command(self, message: TelegramMessage) -> None:
        """Показать статус бота и конфигурацию"""
        from application.settings import get_config

        from .decorators import get_user_role

        config = get_config()
        user_role = get_user_role(message.from_user.id)
        warnings_limit = await self.moderation_service.get_warnings_limit(message.chat.id)
        forbidden_count = len(await self.moderation_service.get_forbidden_words())

        status_text = (
            f"🤖 **Статус бота**\n\n"
            f"👤 Ваша роль: {user_role}\n"
            f"⚠️ Лимит предупреждений: {warnings_limit}\n"
            f"🚫 Запрещенных слов: {forbidden_count}\n"
            f"🏷️ Версия: {config.environment}"
        )

        await message.reply(status_text, parse_mode="Markdown")

    async def help_command(self, message: TelegramMessage) -> None:
        """Показать справку по командам"""
        from .decorators import get_user_role

        user_role = get_user_role(message.from_user.id)

        help_text = "🤖 **Справка по командам**\n\n"

        if user_role in ["owner", "admin"]:
            help_text += (
                "**Команды администратора:**\n"
                "/add_forbidden <слово> - добавить запрещенное слово\n"
                "/remove_forbidden <слово> - удалить запрещенное слово\n"
                "/list_forbidden - показать запрещенные слова\n"
                "/set_warnings <число> - установить лимит предупреждений\n"
                "/bot_status - статус бота\n\n"
            )

        if user_role == "owner":
            help_text += "**Команды владельца:**\n" "/clear_forbidden - очистить все запрещенные слова\n\n"

        help_text += (
            "**Команды модерации (для админов чата):**\n"
            "/ban - забанить пользователя (ответом на сообщение)\n"
            "/unban - разбанить пользователя\n"
            "/mute - заглушить пользователя\n"
            "/unmute - снять заглушение\n"
            "/kick - исключить из чата\n\n"
            "**Общие команды:**\n"
            "/help - эта справка"
        )

        await message.reply(help_text, parse_mode="Markdown")

    async def _get_target_user(self, message: TelegramMessage) -> Optional[User]:
        """Получить целевого пользователя из ответного сообщения"""
        if not message.reply_to_message or not message.reply_to_message.from_user:
            await message.reply("Эта команда должна использоваться как ответ на сообщение")
            return None

        target_id = message.reply_to_message.from_user.id

        # Не разрешаем модерировать самого бота
        if target_id == message.bot.id:
            await message.reply("Я не могу модерировать сам себя")
            return None

        # Проверяем, существует ли пользователь в нашей базе данных
        user = await self.user_repository.get_by_id(target_id, message.chat.id)
        if not user:
            user = User(target_id, message.chat.id)

        return user
