from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest

from application.services.moderation_service import TelegramModerationService
from application.settings import ModerationConfig
from domain.entities.message import Message
from domain.entities.user import User
from domain.exceptions import UserAlreadyBannedError, UserAlreadyMutedError, UserNotBannedError, UserNotMutedError


@pytest.fixture
def config():
    """Mock конфигурации модерации"""
    config = AsyncMock()
    config.get_warnings_limit.return_value = 3
    config.set_warnings_limit = AsyncMock()
    config.add_forbidden_word = AsyncMock()
    config.remove_forbidden_word = AsyncMock()
    config.get_forbidden_words.return_value = ["bad", "word"]
    config.check_text.return_value = []
    config.clear_forbidden_words = AsyncMock()
    return config


@pytest.fixture
def user_repository(user):
    """Mock репозитория пользователей, возвращающий реальный объект User"""
    repo = AsyncMock()
    repo.get_by_id.return_value = user
    repo.save = AsyncMock()
    return repo


@pytest.fixture
def message_repository():
    return AsyncMock()


@pytest.fixture
def service(user_repository, message_repository, config):
    return TelegramModerationService(user_repository=user_repository, message_repository=message_repository, config=config)


@pytest.fixture
def user():
    return User(user_id=123, chat_id=456)


@pytest.fixture
def message():
    return Message(message_id=1, user_id=123, chat_id=456, text="test message", timestamp=datetime.utcnow())


@pytest.mark.asyncio
async def test_check_message_no_violations(service, message):
    violations = await service.check_message(message)
    assert not violations
    assert not message.contains_violations
    assert not message.violation_words


@pytest.mark.asyncio
async def test_check_message_with_violations(service, message, config):
    # Настраиваем мок config для возврата нарушений
    config.check_text.return_value = ["bad", "word"]
    message.text = "this is a bad word"
    violations = await service.check_message(message)
    assert violations == ["bad", "word"]
    assert message.contains_violations
    assert message.violation_words == ["bad", "word"]


@pytest.mark.asyncio
async def test_warn_user(service, user, user_repository):
    await service.warn_user(user, ["bad"])
    assert user.warnings_count == 1
    assert user.last_warning_time is not None
    user_repository.save.assert_awaited_once_with(user)


@pytest.mark.asyncio
async def test_warn_user_exceeds_limit(service, user, user_repository, config):
    # Настраиваем лимит предупреждений на 3
    config.get_warnings_limit.return_value = 3
    user.warnings_count = 2  # One warning away from default limit of 3
    await service.warn_user(user, ["bad"])
    assert user.warnings_count == 3
    assert user.is_banned
    assert not user.can_send_messages


@pytest.mark.asyncio
async def test_ban_user(service, user, user_repository):
    await service.ban_user(user)
    assert user.is_banned
    assert not user.can_send_messages
    user_repository.save.assert_awaited_once_with(user)


@pytest.mark.asyncio
async def test_ban_already_banned_user(service, user):
    user.is_banned = True
    with pytest.raises(UserAlreadyBannedError):
        await service.ban_user(user)


@pytest.mark.asyncio
async def test_unban_user(service, user, user_repository):
    user.is_banned = True
    user.can_send_messages = False
    await service.unban_user(user)
    assert not user.is_banned
    assert user.can_send_messages
    assert user.warnings_count == 0
    user_repository.save.assert_awaited_once_with(user)


@pytest.mark.asyncio
async def test_unban_not_banned_user(service, user):
    with pytest.raises(UserNotBannedError):
        await service.unban_user(user)


@pytest.mark.asyncio
async def test_mute_user(service, user, user_repository):
    await service.mute_user(user)
    assert not user.can_send_messages
    user_repository.save.assert_awaited_once_with(user)


@pytest.mark.asyncio
async def test_mute_already_muted_user(service, user):
    user.can_send_messages = False
    with pytest.raises(UserAlreadyMutedError):
        await service.mute_user(user)


@pytest.mark.asyncio
async def test_unmute_user(service, user, user_repository):
    user.can_send_messages = False
    await service.unmute_user(user)
    assert user.can_send_messages
    user_repository.save.assert_awaited_once_with(user)


@pytest.mark.asyncio
async def test_unmute_not_muted_user(service, user):
    with pytest.raises(UserNotMutedError):
        await service.unmute_user(user)


@pytest.mark.asyncio
async def test_kick_user(service, user, user_repository):
    user.warnings_count = 2
    user.is_banned = True
    await service.kick_user(user)
    assert user.warnings_count == 0
    assert not user.is_banned
    assert user.can_send_messages
    user_repository.save.assert_awaited_once_with(user)


@pytest.mark.asyncio
async def test_check_message_with_empty_text(service):
    """Тест проверки сообщения с пустым текстом"""
    message = Message(message_id=1, user_id=123, chat_id=456, text="", timestamp=datetime.utcnow())
    violations = await service.check_message(message)
    assert not violations


@pytest.mark.asyncio
async def test_check_message_with_none_text(service):
    """Тест проверки сообщения с None текстом"""
    message = Message(message_id=1, user_id=123, chat_id=456, text=None, timestamp=datetime.utcnow())
    violations = await service.check_message(message)
    assert not violations


@pytest.mark.asyncio
async def test_warn_user_multiple_violations(service, user, user_repository):
    """Тест предупреждения с несколькими нарушениями"""
    await service.warn_user(user, ["bad", "word", "spam"])
    assert user.warnings_count == 1
    assert user.last_warning_time is not None
    user_repository.save.assert_awaited_once_with(user)


@pytest.mark.asyncio
async def test_service_with_custom_warnings_limit(user_repository, message_repository):
    """Тест сервиса с кастомным лимитом предупреждений"""
    from application.enhanced_config import EnhancedModerationConfig

    config = EnhancedModerationConfig()

    service = TelegramModerationService(user_repository=user_repository, message_repository=message_repository, config=config)

    user = User(user_id=123, chat_id=456)
    user.warnings_count = 4

    # Мокаем get_warnings_limit чтобы вернуть 5
    with patch.object(service, "get_warnings_limit", return_value=5):
        await service.warn_user(user, ["bad"])
        assert user.warnings_count == 5
        assert user.is_banned
        assert not user.can_send_messages


@pytest.mark.asyncio
async def test_is_message_violation_case_insensitive(service, config):
    """Тест проверки регистронезависимости"""
    # Настраиваем мок для возврата нарушений
    config.check_text.return_value = ["bad", "word"]
    message = Message(message_id=1, user_id=123, chat_id=456, text="This is a BAD WORD", timestamp=datetime.utcnow())
    violations = await service.check_message(message)
    assert "bad" in violations
    assert "word" in violations


@pytest.mark.asyncio
async def test_user_state_consistency_after_ban(service, user, user_repository):
    """Тест консистентности состояния пользователя после бана"""
    await service.ban_user(user)

    # Проверяем все аспекты забаненного пользователя
    assert user.is_banned is True
    assert user.can_send_messages is False

    # Проверяем что репозиторий вызван для сохранения
    user_repository.save.assert_awaited_once_with(user)


@pytest.mark.asyncio
async def test_user_state_consistency_after_unban(service, user, user_repository):
    """Тест консистентности состояния пользователя после разбана"""
    user.is_banned = True
    user.can_send_messages = False
    user.warnings_count = 3

    await service.unban_user(user)

    # Проверяем все аспекты разбаненного пользователя
    assert user.is_banned is False
    assert user.can_send_messages is True
    assert user.warnings_count == 0  # Предупреждения должны сброситься

    user_repository.save.assert_awaited_once_with(user)


@pytest.mark.asyncio
async def test_check_message_creates_new_user_when_none_exists(service, message_repository):
    """Тест создания нового пользователя при его отсутствии в check_message"""
    # Настраиваем mock для возврата None из user_repository.get_by_id
    service.user_repository.get_by_id.return_value = None

    # Настраиваем config для обнаружения нарушений
    service.config.check_text.return_value = ["badword"]

    # Мокаем warn_user
    service.warn_user = AsyncMock()

    message = Message(message_id=1, user_id=999, chat_id=777, text="This contains badword", timestamp=datetime.utcnow())

    violation_words = await service.check_message(message)

    # Проверяем что был создан новый пользователь и передан в warn_user
    assert violation_words == ["badword"]
    service.warn_user.assert_awaited_once()

    # Проверяем что warn_user был вызван с новым пользователем
    called_user = service.warn_user.call_args[0][0]
    assert called_user.user_id == 999
    assert called_user.chat_id == 777


@pytest.mark.asyncio
async def test_set_warnings_limit(service):
    """Тест установки лимита предупреждений"""
    chat_id = 123
    limit = 5

    await service.set_warnings_limit(chat_id, limit)

    service.config.set_warnings_limit.assert_awaited_once_with(chat_id, limit)


@pytest.mark.asyncio
async def test_add_forbidden_word(service):
    """Тест добавления запрещенного слова"""
    word = "newbadword"

    await service.add_forbidden_word(word)

    service.config.add_forbidden_word.assert_awaited_once_with(word)


@pytest.mark.asyncio
async def test_remove_forbidden_word(service):
    """Тест удаления запрещенного слова"""
    word = "badword"
    service.config.remove_forbidden_word.return_value = True

    result = await service.remove_forbidden_word(word)

    assert result is True
    service.config.remove_forbidden_word.assert_awaited_once_with(word)


@pytest.mark.asyncio
async def test_get_forbidden_words(service):
    """Тест получения списка запрещенных слов"""
    expected_words = ["bad", "word", "evil"]
    service.config.get_forbidden_words.return_value = expected_words

    words = await service.get_forbidden_words()

    assert words == expected_words
    service.config.get_forbidden_words.assert_awaited_once()


@pytest.mark.asyncio
async def test_clear_forbidden_words(service):
    """Тест очистки всех запрещенных слов"""
    await service.clear_forbidden_words()

    service.config.clear_forbidden_words.assert_awaited_once()
