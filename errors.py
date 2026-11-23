"""Custom exceptions used across QueryLens AI."""


class ValidationError(ValueError):
    """Raised when user input (question, FAQ field, threshold...) is invalid."""


class DatabaseError(RuntimeError):
    """Raised when a SQLite operation fails."""


class NotFoundError(LookupError):
    """Raised when a requested record does not exist."""
