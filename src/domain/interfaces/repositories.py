from abc import ABC, abstractmethod
from typing import List, Optional

from domain.entities.message import Message
from domain.entities.user import User


class UserRepository(ABC):
    @abstractmethod
    async def get_by_id(self, user_id: int, chat_id: int) -> Optional[User]:
        pass

    @abstractmethod
    async def save(self, user: User) -> None:
        pass

    @abstractmethod
    async def update_warnings(self, user_id: int, chat_id: int, warnings_count: int) -> None:
        pass


class MessageRepository(ABC):
    @abstractmethod
    async def save(self, message: Message) -> None:
        pass

    @abstractmethod
    async def get_user_violations(self, user_id: int, chat_id: int) -> List[Message]:
        pass

    @abstractmethod
    async def get_recent_messages(self, chat_id: int, limit: int = 100) -> List[Message]:
        pass
