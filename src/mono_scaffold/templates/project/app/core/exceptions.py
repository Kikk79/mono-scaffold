"""Fachfehler. Antwort ist immer JSON `{code, message}`; Meldung deutsch, sagt was zu tun ist.

Services werfen nur diese Klassen. Ein `IntegrityError` beim Flush wird im Service zu
`ConflictError`. Unbehandelte Ausnahmen werden in `app/main.py` zu 500 `internal_error`.
"""

from __future__ import annotations


class AppError(Exception):
    status_code = 500
    code = "internal_error"

    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        if code:
            self.code = code


class UnauthorizedError(AppError):
    status_code = 401
    code = "unauthorized"


class ForbiddenError(AppError):
    status_code = 403
    code = "forbidden"


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"


class ConflictError(AppError):
    status_code = 409
    code = "conflict"


class PayloadTooLargeError(AppError):
    status_code = 413
    code = "payload_too_large"


class ValidationAppError(AppError):
    status_code = 422
    code = "validation_error"


class TooManyRequestsError(AppError):
    status_code = 429
    code = "too_many_requests"
