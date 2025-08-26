from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, validator


class MessageData(BaseModel):
    """Модель валидации данных сообщения"""

    message_id: int = Field(..., gt=0, description="ID сообщения должен быть положительным")
    user_id: int = Field(..., gt=0, description="ID пользователя должен быть положительным")
    chat_id: int = Field(..., description="ID чата")
    text: str = Field(..., min_length=1, max_length=4096, description="Текст сообщения")
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)

    @validator("text")
    def text_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Текст сообщения не может быть пустым")
        return v.strip()

    @validator("chat_id")
    def chat_id_valid(cls, v):
        if v == 0:
            raise ValueError("ID чата не может быть равен нулю")
        return v

    class Config:
        str_strip_whitespace = True
        validate_assignment = True


class UserData(BaseModel):
    """Модель валидации данных пользователя"""

    user_id: int = Field(..., gt=0, description="ID пользователя должен быть положительным")
    chat_id: int = Field(..., description="ID чата")
    warnings_count: int = Field(default=0, ge=0, description="Количество предупреждений не может быть отрицательным")
    is_banned: bool = Field(default=False)
    can_send_messages: bool = Field(default=True)
    last_warning_time: Optional[datetime] = None

    @validator("chat_id")
    def chat_id_valid(cls, v):
        if v == 0:
            raise ValueError("ID чата не может быть равен нулю")
        return v

    class Config:
        validate_assignment = True


class ForbiddenWordData(BaseModel):
    """Модель валидации запрещенного слова"""

    word: str = Field(..., min_length=1, max_length=100, description="Запрещенное слово")
    chat_id: int = Field(..., description="ID чата")

    @validator("word")
    def word_valid(cls, v):
        v = v.lower().strip()
        if not v:
            raise ValueError("Запрещенное слово не может быть пустым")
        if len(v.split()) > 3:
            raise ValueError("Запрещенное слово не может содержать более 3 слов")
        return v

    @validator("chat_id")
    def chat_id_valid(cls, v):
        if v == 0:
            raise ValueError("ID чата не может быть равен нулю")
        return v

    class Config:
        str_strip_whitespace = True
        validate_assignment = True


class WarningsLimitData(BaseModel):
    """Модель валидации лимита предупреждений"""

    chat_id: int = Field(..., description="ID чата")
    limit: int = Field(..., ge=1, le=100, description="Лимит предупреждений должен быть от 1 до 100")

    @validator("chat_id")
    def chat_id_valid(cls, v):
        if v == 0:
            raise ValueError("ID чата не может быть равен нулю")
        return v

    class Config:
        validate_assignment = True


class BotCommandData(BaseModel):
    """Модель валидации команды бота"""

    command: str = Field(..., min_length=1, max_length=50)
    args: List[str] = Field(default_factory=list)
    user_id: int = Field(..., gt=0)
    chat_id: int = Field(...)
    message_id: int = Field(..., gt=0)

    @validator("command")
    def command_valid(cls, v):
        v = v.lower().strip()
        if not v.startswith("/"):
            v = "/" + v
        return v

    @validator("args")
    def args_valid(cls, v):
        return [arg.strip() for arg in v if arg.strip()]

    class Config:
        str_strip_whitespace = True
        validate_assignment = True
