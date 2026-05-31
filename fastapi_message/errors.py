from __future__ import annotations


class MessageError(Exception):
    def __init__(
        self,
        message: str,
        *,
        service_name: str | None = None,
        action_name: str | None = None,
        path: str | None = None,
        status_code: int | None = None,
        request_id: str | None = None,
        error_code: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.service_name = service_name
        self.action_name = action_name
        self.path = path
        self.status_code = status_code
        self.request_id = request_id
        self.error_code = error_code

    def to_dict(self) -> dict:
        return {
            "error": {
                "code": self.error_code or self.__class__.__name__,
                "message": self.message,
                "request_id": self.request_id,
            }
        }


class ConfigError(MessageError):
    pass


class RegistryError(MessageError):
    pass


class ActionNotFoundError(MessageError):
    pass


class NetworkError(MessageError):
    pass


class TimeoutError(MessageError):
    pass


class DecodeError(MessageError):
    pass


class RemoteError(MessageError):
    pass


class UnauthorizedError(RemoteError):
    pass


class ForbiddenError(RemoteError):
    pass


class NotFoundError(RemoteError):
    pass


class ConflictError(RemoteError):
    pass


class PayloadTooLargeError(RemoteError):
    pass


class RateLimitedError(RemoteError):
    pass


class UpstreamError(RemoteError):
    pass


STATUS_ERROR_MAP = {
    401: UnauthorizedError,
    403: ForbiddenError,
    404: NotFoundError,
    409: ConflictError,
    413: PayloadTooLargeError,
    429: RateLimitedError,
    500: UpstreamError,
    502: UpstreamError,
    503: UpstreamError,
    504: UpstreamError,
}
