from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, Table, UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class UserModel(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    chat_id = Column(Integer, nullable=False)
    warnings_count = Column(Integer, default=0)
    is_banned = Column(Boolean, default=False)
    can_send_messages = Column(Boolean, default=True)
    last_warning_time = Column(DateTime, nullable=True)

    messages = relationship("MessageModel", back_populates="user")

    __table_args__ = (
        # Составной уникальный индекс для user_id и chat_id
        # так как пользователь может быть в нескольких чатах
        UniqueConstraint("user_id", "chat_id", name="uq_user_chat"),
    )

    def __init__(self, user_id=None, chat_id=None, **kwargs):
        super().__init__(**kwargs)
        if user_id is not None:
            self.user_id = user_id
        if chat_id is not None:
            self.chat_id = chat_id
        # Устанавливаем default значения, если они не были переданы
        if "warnings_count" not in kwargs:
            self.warnings_count = 0
        if "is_banned" not in kwargs:
            self.is_banned = False
        if "can_send_messages" not in kwargs:
            self.can_send_messages = True

    def __repr__(self):
        return f"<UserModel(user_id={self.user_id}, chat_id={self.chat_id}, warnings={self.warnings_count}, banned={self.is_banned})>"


class MessageModel(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True)
    message_id = Column(Integer, nullable=False)
    chat_id = Column(Integer, nullable=False)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    text = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    contains_violations = Column(Boolean, default=False)
    violation_words = Column(JSON, nullable=True)

    user = relationship("UserModel", back_populates="messages")

    def __init__(self, message_id=None, chat_id=None, user_id=None, text=None, **kwargs):
        super().__init__(**kwargs)
        if message_id is not None:
            self.message_id = message_id
        if chat_id is not None:
            self.chat_id = chat_id
        if user_id is not None:
            self.user_id = user_id
        if text is not None:
            self.text = text
        # Устанавливаем default значения, если они не были переданы
        if "timestamp" not in kwargs:
            self.timestamp = datetime.utcnow()
        if "contains_violations" not in kwargs:
            self.contains_violations = False

    def __repr__(self):
        return f"<MessageModel(message_id={self.message_id}, chat_id={self.chat_id}, user_id={self.user_id}, text='{self.text[:50]}...')>"


class ChatConfigModel(Base):
    __tablename__ = "chat_configs"

    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, unique=True, nullable=False)
    warnings_limit = Column(Integer, default=3)
    forbidden_words = Column(JSON, nullable=False, default=list)
