"""Custom exception hierarchy for structured error responses.

See DECISIONS.md DEC-05 for rationale (custom hierarchy over RFC 7807).
"""


class AppError(Exception):
    """Base exception for all application errors."""

    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.status_code = status_code


class NotFoundError(AppError):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)


class ValidationError(AppError):
    def __init__(self, message: str = "Validation error"):
        super().__init__(message, status_code=422)


class ServiceUnavailableError(AppError):
    def __init__(self, message: str = "Service unavailable"):
        super().__init__(message, status_code=503)


class CrewExecutionError(AppError):
    def __init__(self, message: str = "Crew execution failed"):
        super().__init__(message, status_code=500)


class VoiceDisabledError(AppError):
    """Raised when a voice-tool call is attempted while VOICE_ENABLED=false (slice-26, DEC-22)."""

    def __init__(self, message: str = "Voice features are disabled. Set VOICE_ENABLED=true to enable."):
        super().__init__(message, status_code=422)
