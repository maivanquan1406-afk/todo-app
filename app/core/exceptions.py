from typing import Optional

class AppError(Exception):
    """Base class for application-specific exceptions."""

    def __init__(self, message: str = "Application error", *, code: Optional[str] = None):
        super().__init__(message)
        self.code = code


class DatabaseError(AppError):
    """Raised when database operations fail."""

    def __init__(self, message: str = "Database error", *, original: Optional[Exception] = None):
        super().__init__(message, code="database_error")
        self.original = original


class NotFoundError(AppError):
    """Raised when an entity cannot be found."""

    def __init__(self, resource: str = "resource", message: str | None = None):
        detail = message or f"{resource} not found"
        super().__init__(detail, code="not_found")
        self.resource = resource


class ConflictError(AppError):
    """Raised when attempting to create a resource that conflicts with existing data."""

    def __init__(self, message: str = "Resource conflict"):
        super().__init__(message, code="conflict")


class ValidationError(AppError):
    """Raised when business validation fails."""

    def __init__(self, message: str = "Validation error", *, field: Optional[str] = None):
        super().__init__(message, code="validation_error")
        self.field = field


class AuthenticationError(AppError):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, code="authentication_error")


class EmailError(AppError):
    """Raised when outbound email sending fails."""

    def __init__(self, message: str = "Email delivery failed"):
        super().__init__(message, code="email_error")
