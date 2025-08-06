class AutoVideoException(Exception):
    """基礎異常類"""

    def __init__(self, message: str, error_code: str = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class ValidationError(AutoVideoException):
    """驗證錯誤"""



class AuthenticationError(AutoVideoException):
    """認證錯誤"""



class AuthorizationError(AutoVideoException):
    """授權錯誤"""



class ResourceNotFoundError(AutoVideoException):
    """資源未找到錯誤"""



class ServiceUnavailableError(AutoVideoException):
    """服務不可用錯誤"""



class RateLimitError(AutoVideoException):
    """速率限制錯誤"""

