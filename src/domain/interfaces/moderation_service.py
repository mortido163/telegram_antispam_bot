from abc import ABC, abstractmethod
from typing import List

from domain.entities.message import Message
from domain.entities.user import User


class ModerationService(ABC):
    @abstractmethod
    async def check_message(self, message: Message) -> List[str]:
        """Check message for violations and return list of found forbidden words"""
        pass

    @abstractmethod
    async def warn_user(self, user: User, violation_words: List[str]) -> None:
        """Issue a warning to a user for using forbidden words"""
        pass

    @abstractmethod
    async def ban_user(self, user: User) -> None:
        """Ban user from the chat"""
        pass

    @abstractmethod
    async def unban_user(self, user: User) -> None:
        """Remove ban from the user"""
        pass

    @abstractmethod
    async def mute_user(self, user: User) -> None:
        """Restrict user from sending messages"""
        pass

    @abstractmethod
    async def unmute_user(self, user: User) -> None:
        """Allow user to send messages"""
        pass

    @abstractmethod
    async def kick_user(self, user: User) -> None:
        """Remove user from the chat"""
        pass

    @abstractmethod
    async def get_warnings_limit(self, chat_id: int) -> int:
        """Get the number of warnings before ban for specific chat"""
        pass

    @abstractmethod
    async def set_warnings_limit(self, chat_id: int, limit: int) -> None:
        """Set the number of warnings before ban for specific chat"""
        pass
