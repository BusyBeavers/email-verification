from __future__ import annotations

from fastapi import status


class ApiError(Exception):
    def __init__(self, error: str, message: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        self.error = error
        self.message = message
        self.status_code = status_code
        super().__init__(message)
