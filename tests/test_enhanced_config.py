from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from src.application.enhanced_config import EnhancedModerationConfig
from src.infrastructure.database.models import ChatConfigModel


class TestEnhancedModerationConfig:
    """Тесты для класса EnhancedModerationConfig"""

    @pytest.fixture
    def mock_session_manager(self):
        """Фикстура для мокирования session manager"""
        mock_session = AsyncMock()
        mock_session_manager = MagicMock()
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__.return_value = mock_session
        mock_context_manager.__aexit__.return_value = None
        mock_session_manager.session.return_value = mock_context_manager
        return mock_session_manager, mock_session

    @pytest.fixture
    def config(self):
        """Фикстура для создания экземпляра конфигурации"""
        return EnhancedModerationConfig()

    @pytest.fixture
    def mock_chat_config(self):
        """Фикстура для мока конфигурации чата"""
        mock_config = Mock(spec=ChatConfigModel)
        mock_config.warnings_limit = 3
        mock_config.forbidden_words = ["spam", "bad"]
        return mock_config

    @pytest.mark.asyncio
    async def test_set_warnings_limit_valid(self, config, mock_chat_config, mock_session_manager):
        """Тест установки валидного лимита предупреждений"""
        mock_session_manager_obj, mock_session = mock_session_manager

        with patch.object(config, "_get_or_create_chat_config", return_value=mock_chat_config):
            with patch("src.application.enhanced_config.get_session_manager", return_value=mock_session_manager_obj):
                await config.set_warnings_limit(123456, 5)

        assert mock_chat_config.warnings_limit == 5
        mock_session.add.assert_called_once_with(mock_chat_config)

    @pytest.mark.asyncio
    async def test_set_warnings_limit_invalid(self, config, mock_session_manager):
        """Тест установки невалидного лимита предупреждений"""
        mock_session_manager_obj, mock_session = mock_session_manager

        with patch("src.application.enhanced_config.get_session_manager", return_value=mock_session_manager_obj):
            with pytest.raises(ValueError, match="Лимит предупреждений должен быть положительным"):
                await config.set_warnings_limit(123456, 0)

    @pytest.mark.asyncio
    async def test_get_warnings_limit_from_cache(self, config):
        """Тест получения лимита предупреждений из кэша"""
        mock_config = Mock()
        mock_config.warnings_limit = 5
        config._cached_configs = {123456: mock_config}

        result = await config.get_warnings_limit(123456)
        assert result == 5

    @pytest.mark.asyncio
    async def test_get_warnings_limit_default(self, config):
        """Тест получения лимита предупреждений по умолчанию"""
        with patch.object(config, "_get_chat_config", return_value=None):
            result = await config.get_warnings_limit(123456)

        assert result == config.default_warnings_limit

    @pytest.mark.asyncio
    async def test_add_forbidden_word_valid(self, config, mock_chat_config, mock_session_manager):
        """Тест добавления валидного запрещенного слова"""
        mock_session_manager_obj, mock_session = mock_session_manager

        with patch.object(config, "_get_or_create_chat_config", return_value=mock_chat_config):
            with patch("src.application.enhanced_config.get_session_manager", return_value=mock_session_manager_obj):
                await config.add_forbidden_word(123456, "  NEWWORD  ")

        assert "newword" in mock_chat_config.forbidden_words
        mock_session.add.assert_called_once_with(mock_chat_config)

    @pytest.mark.asyncio
    async def test_add_forbidden_word_empty_string(self, config):
        """Тест добавления пустого запрещенного слова"""
        # Не должно вызывать никаких действий
        await config.add_forbidden_word(123456, "   ")

    @pytest.mark.asyncio
    async def test_add_forbidden_word_with_none_list(self, config, mock_session_manager):
        """Тест добавления слова когда список None"""
        mock_session_manager_obj, mock_session = mock_session_manager
        mock_config = Mock(spec=ChatConfigModel)
        mock_config.forbidden_words = None

        with patch.object(config, "_get_or_create_chat_config", return_value=mock_config):
            with patch("src.application.enhanced_config.get_session_manager", return_value=mock_session_manager_obj):
                await config.add_forbidden_word(123456, "spam")

        assert mock_config.forbidden_words == ["spam"]

    @pytest.mark.asyncio
    async def test_remove_forbidden_word_existing(self, config, mock_session_manager):
        """Тест удаления существующего запрещенного слова"""
        mock_session_manager_obj, mock_session = mock_session_manager
        mock_config = Mock(spec=ChatConfigModel)
        mock_config.forbidden_words = ["spam", "bad"]

        with patch.object(config, "_get_chat_config_from_db", return_value=mock_config):
            with patch("src.application.enhanced_config.get_session_manager", return_value=mock_session_manager_obj):
                await config.remove_forbidden_word(123456, "spam")

        # Проверяем что слово было удалено
        assert "spam" not in mock_config.forbidden_words

    @pytest.mark.asyncio
    async def test_remove_forbidden_word_non_existing(self, config, mock_session_manager):
        """Тест удаления несуществующего запрещенного слова"""
        mock_session_manager_obj, mock_session = mock_session_manager
        mock_config = Mock(spec=ChatConfigModel)
        mock_config.forbidden_words = ["spam", "bad"]
        original_words = mock_config.forbidden_words.copy()

        with patch.object(config, "_get_chat_config_from_db", return_value=mock_config):
            with patch("src.application.enhanced_config.get_session_manager", return_value=mock_session_manager_obj):
                await config.remove_forbidden_word(123456, "nonexistent")

        # Проверяем что список остался неизменным
        assert mock_config.forbidden_words == original_words

    @pytest.mark.asyncio
    async def test_get_forbidden_words_with_config(self, config, mock_chat_config):
        """Тест получения запрещенных слов когда есть конфигурация"""
        with patch.object(config, "_get_chat_config", return_value=mock_chat_config):
            result = await config.get_forbidden_words(123456)

        assert result == ["spam", "bad"]

    @pytest.mark.asyncio
    async def test_get_forbidden_words_no_config(self, config):
        """Тест получения запрещенных слов когда нет конфигурации"""
        with patch.object(config, "_get_chat_config", return_value=None):
            result = await config.get_forbidden_words(123456)

        assert result == []

    @pytest.mark.asyncio
    async def test_check_text_with_violations(self, config):
        """Тест проверки текста с нарушениями"""
        with patch.object(config, "get_forbidden_words", return_value=["spam", "bad"]):
            with patch.object(config, "_get_compiled_patterns") as mock_patterns:
                # Мокируем паттерны
                pattern1 = Mock()
                pattern1.search.return_value = Mock()  # найден
                pattern2 = Mock()
                pattern2.search.return_value = None  # не найден
                mock_patterns.return_value = [pattern1, pattern2]

                result = await config.check_text(123456, "This is spam message")

        assert result == ["spam"]

    @pytest.mark.asyncio
    async def test_check_text_no_violations(self, config):
        """Тест проверки текста без нарушений"""
        with patch.object(config, "get_forbidden_words", return_value=["spam", "bad"]):
            with patch.object(config, "_get_compiled_patterns") as mock_patterns:
                # Мокируем паттерны - ничего не найдено
                pattern1 = Mock()
                pattern1.search.return_value = None
                pattern2 = Mock()
                pattern2.search.return_value = None
                mock_patterns.return_value = [pattern1, pattern2]

                result = await config.check_text(123456, "This is clean message")

        assert result == []

    @pytest.mark.asyncio
    async def test_check_text_empty(self, config):
        """Тест проверки пустого текста"""
        result = await config.check_text(123456, "")
        assert result == []

    @pytest.mark.asyncio
    async def test_check_text_no_forbidden_words(self, config):
        """Тест проверки текста когда нет запрещенных слов"""
        with patch.object(config, "get_forbidden_words", return_value=[]):
            result = await config.check_text(123456, "Any text")

        assert result == []

    @pytest.mark.asyncio
    async def test_clear_forbidden_words(self, config, mock_chat_config, mock_session_manager):
        """Тест очистки всех запрещенных слов"""
        mock_session_manager_obj, mock_session = mock_session_manager

        with patch.object(config, "_get_or_create_chat_config", return_value=mock_chat_config):
            with patch("src.application.enhanced_config.get_session_manager", return_value=mock_session_manager_obj):
                await config.clear_forbidden_words(123456)

        assert mock_chat_config.forbidden_words == []
        mock_session.add.assert_called_once_with(mock_chat_config)

    @pytest.mark.asyncio
    async def test_get_chat_config_from_cache(self, config, mock_chat_config):
        """Тест получения конфигурации чата из кэша"""
        config._cached_configs = {123456: mock_chat_config}

        result = await config._get_chat_config(123456)
        assert result == mock_chat_config

    @pytest.mark.asyncio
    async def test_get_chat_config_from_db(self, config, mock_chat_config, mock_session_manager):
        """Тест получения конфигурации чата из БД"""
        mock_session_manager_obj, mock_session = mock_session_manager

        with patch.object(config, "_get_chat_config_from_db", return_value=mock_chat_config):
            with patch("src.application.enhanced_config.get_session_manager", return_value=mock_session_manager_obj):
                result = await config._get_chat_config(123456)

        assert result == mock_chat_config
        assert config._cached_configs[123456] == mock_chat_config

    @pytest.mark.asyncio
    async def test_get_chat_config_from_db_error(self, config, mock_session_manager):
        """Тест обработки ошибки при получении конфигурации из БД"""
        mock_session_manager_obj, mock_session = mock_session_manager

        with patch.object(config, "_get_chat_config_from_db", side_effect=Exception("DB Error")):
            with patch("src.application.enhanced_config.get_session_manager", return_value=mock_session_manager_obj):
                result = await config._get_chat_config(123456)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_chat_config_from_db_method(self, config, mock_chat_config, mock_session_manager):
        """Тест метода получения конфигурации из БД"""
        mock_session_manager_obj, mock_session = mock_session_manager
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_chat_config
        mock_session.execute.return_value = mock_result

        result = await config._get_chat_config_from_db(mock_session, 123456)
        assert result == mock_chat_config

    @pytest.mark.asyncio
    async def test_get_or_create_chat_config_existing(self, config, mock_chat_config, mock_session_manager):
        """Тест получения существующей конфигурации чата"""
        mock_session_manager_obj, mock_session = mock_session_manager

        with patch.object(config, "_get_chat_config_from_db", return_value=mock_chat_config):
            result = await config._get_or_create_chat_config(mock_session, 123456)

        assert result == mock_chat_config

    @pytest.mark.asyncio
    async def test_get_or_create_chat_config_new(self, config, mock_session_manager):
        """Тест создания новой конфигурации чата"""
        mock_session_manager_obj, mock_session = mock_session_manager

        with patch.object(config, "_get_chat_config_from_db", return_value=None):
            with patch("src.application.enhanced_config.ChatConfigModel") as mock_chat_config_class:
                mock_new_config = Mock()
                mock_chat_config_class.return_value = mock_new_config

                result = await config._get_or_create_chat_config(mock_session, 123456)

        assert result == mock_new_config
        mock_chat_config_class.assert_called_once_with(
            chat_id=123456, warnings_limit=config.default_warnings_limit, forbidden_words=[]
        )

    @pytest.mark.asyncio
    async def test_get_compiled_patterns_caching(self, config):
        """Тест кэширования скомпилированных паттернов"""
        words = ["spam", "bad"]

        # Первый вызов
        patterns1 = await config._get_compiled_patterns(123456, words)
        # Второй вызов - должен вернуть из кэша
        patterns2 = await config._get_compiled_patterns(123456, words)

        assert patterns1 is patterns2
        assert len(patterns1) == 2

    def test_invalidate_patterns_cache(self, config):
        """Тест инвалидации кэша паттернов"""
        config._compiled_patterns_cache = {"123456_123": Mock(), "123456_456": Mock(), "789012_789": Mock()}

        config._invalidate_patterns_cache(123456)

        assert "123456_123" not in config._compiled_patterns_cache
        assert "123456_456" not in config._compiled_patterns_cache
        assert "789012_789" in config._compiled_patterns_cache

    def test_clear_cache_specific_chat(self, config, mock_chat_config):
        """Тест очистки кэша для конкретного чата"""
        config._cached_configs = {123456: mock_chat_config, 789012: Mock()}
        config._compiled_patterns_cache = {"123456_123": Mock()}

        config.clear_cache(123456)

        assert 123456 not in config._cached_configs
        assert "123456_123" not in config._compiled_patterns_cache

    def test_clear_cache_all(self, config, mock_chat_config):
        """Тест очистки всего кэша"""
        config._cached_configs = {123456: mock_chat_config}
        config._compiled_patterns_cache = {"123456_123": Mock()}

        config.clear_cache()

        assert config._cached_configs == {}
        assert config._compiled_patterns_cache == {}
