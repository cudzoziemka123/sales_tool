class AppError(Exception):
    """Base application error with stable machine-readable code."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "ERR_INTERNAL",
        status_code: int = 500,
        retryable: bool = False,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.status_code = status_code
        self.retryable = retryable


class ValidationAppError(AppError):
    def __init__(self, message: str, *, code: str = "ERR_VALIDATION") -> None:
        super().__init__(message, code=code, status_code=400, retryable=False)


class ExternalServiceAppError(AppError):
    def __init__(self, message: str, *, code: str = "ERR_EXTERNAL_SERVICE", retryable: bool = True) -> None:
        super().__init__(message, code=code, status_code=502, retryable=retryable)


class ExternalTimeoutAppError(AppError):
    def __init__(self, message: str, *, code: str = "ERR_EXTERNAL_TIMEOUT") -> None:
        super().__init__(message, code=code, status_code=504, retryable=True)


class ConfigAppError(AppError):
    def __init__(self, message: str, *, code: str = "ERR_CONFIG") -> None:
        super().__init__(message, code=code, status_code=500, retryable=False)


class StorageAppError(AppError):
    def __init__(self, message: str, *, code: str = "ERR_STORAGE") -> None:
        super().__init__(message, code=code, status_code=500, retryable=True)


class NotFoundAppError(AppError):
    def __init__(self, message: str, *, code: str = "ERR_NOT_FOUND") -> None:
        super().__init__(message, code=code, status_code=404, retryable=False)


class UploadTooLargeAppError(AppError):
    def __init__(self, message: str, *, code: str = "ERR_UPLOAD_TOO_LARGE") -> None:
        super().__init__(message, code=code, status_code=413, retryable=False)
