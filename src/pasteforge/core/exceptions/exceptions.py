from typing import Literal

from fastapi import status


class AppException(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(message)


class ValidationError(AppException):
    def __init__(self, message: str = "Validation Error"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, message=message)


class AuthenticationError(AppException):
    def __init__(self, message: str = "Authentication failed."):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, message=message)


class InvalidTokenError(AuthenticationError):
    def __init__(self, token_type: Literal["access", "refresh"], message: str = "Invalid or expired token."):
        super().__init__(message=message)
        self.token_type = token_type


class TooManyRequestsError(AppException):
    def __init__(self, message: str = "Too many requests, Please try again later.", retry_after: int | None = None):
        super().__init__(status_code=status.HTTP_429_TOO_MANY_REQUESTS, message=message)
        self.retry_after = retry_after


class ForbiddenError(AppException):
    def __init__(self, message: str = "Forbidden."):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, message=message)


class UserAlreadyExistsError(AppException):
    def __init__(self, message: str = "User with this email already exists."):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, message=message)


class NotFoundError(AppException):
    def __init__(self, message: str = "Not found."):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, message=message)
