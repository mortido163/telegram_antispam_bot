from dataclasses import dataclass
from datetime import datetime


@dataclass
class Message:
    message_id: int
    user_id: int
    chat_id: int
    text: str
    timestamp: datetime
    contains_violations: bool = False
    violation_words: list[str] = None

    def __post_init__(self):
        if self.violation_words is None:
            self.violation_words = []
