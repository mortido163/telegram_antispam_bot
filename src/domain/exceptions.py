class DomainException(Exception):
    """Base exception for domain errors"""

    pass


class UnauthorizedError(DomainException):
    """Raised when user is not authorized to perform action"""

    pass


class UserNotFoundError(DomainException):
    """Raised when user is not found in the repository"""

    pass


class UserAlreadyBannedError(DomainException):
    """Raised when trying to ban an already banned user"""

    pass


class UserNotBannedError(DomainException):
    """Raised when trying to unban a user who is not banned"""

    pass


class InvalidWarningsLimitError(DomainException):
    """Raised when trying to set invalid warnings limit"""

    pass


class UserAlreadyMutedError(DomainException):
    """Raised when trying to mute an already muted user"""

    pass


class UserNotMutedError(DomainException):
    """Raised when trying to unmute a user who is not muted"""

    pass
