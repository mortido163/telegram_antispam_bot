import re
from dataclasses import dataclass
from typing import Dict, List, Set


@dataclass
class ModerationConfig:
    forbidden_words: List[str]
    warnings_limits: Dict[int, int]  # chat_id -> лимит предупреждений
    default_warnings_limit: int = 3
    _compiled_patterns: Set[re.Pattern] = None  # Кэш скомпилированных регулярных выражений

    @classmethod
    def create_default(cls) -> "ModerationConfig":
        return cls(forbidden_words=[], warnings_limits={}, default_warnings_limit=3)

    def get_warnings_limit(self, chat_id: int) -> int:
        """Получить лимит предупреждений для конкретного чата или вернуть значение по умолчанию"""
        return self.warnings_limits.get(chat_id, self.default_warnings_limit)

    def set_warnings_limit(self, chat_id: int, limit: int) -> None:
        """Установить лимит предупреждений для конкретного чата"""
        if limit < 1:
            raise ValueError("Лимит предупреждений должен быть положительным")
        self.warnings_limits[chat_id] = limit

    def add_forbidden_word(self, word: str) -> None:
        """Добавить новое запрещенное слово в список"""
        word = word.lower().strip()
        if word and word not in self.forbidden_words:
            self.forbidden_words.append(word)
            self._invalidate_pattern_cache()

    def remove_forbidden_word(self, word: str) -> None:
        """Удалить слово из списка запрещенных слов"""
        word = word.lower().strip()
        if word in self.forbidden_words:
            self.forbidden_words.remove(word)
            self._invalidate_pattern_cache()

    def check_text(self, text: str) -> List[str]:
        """Проверить текст на запрещенные слова и вернуть список найденных слов"""
        if not text or not self.forbidden_words:
            return []

        text_lower = text.lower()
        found_words = []

        # Используем кэшированные паттерны для лучшей производительности
        patterns = self._get_compiled_patterns()

        for word, pattern in zip(self.forbidden_words, patterns):
            if pattern.search(text_lower):
                found_words.append(word)

        return found_words

    def _get_compiled_patterns(self) -> List[re.Pattern]:
        """Получить скомпилированные регулярные выражения для запрещенных слов"""
        if self._compiled_patterns is None:
            self._compiled_patterns = []
            for word in self.forbidden_words:
                # Создаем паттерн для поиска слова как отдельного слова (не часть другого слова)
                pattern = re.compile(r"\b" + re.escape(word) + r"\b", re.IGNORECASE)
                self._compiled_patterns.append(pattern)

        return self._compiled_patterns

    def _invalidate_pattern_cache(self) -> None:
        """Сбросить кэш скомпилированных паттернов"""
        self._compiled_patterns = None
