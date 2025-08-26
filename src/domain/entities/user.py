from dataclasses import dataclass
from datetime import datetime


@dataclass
class User:
    user_id: int
    chat_id: int
    warnings_count: int = 0
    is_banned: bool = False
    can_send_messages: bool = True
    last_warning_time: datetime | None = None
