class AgentForgeException(Exception):
    def __init__(self, message: str, code: str = "error", status_code: int = 400):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)

class NotFoundError(AgentForgeException):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, code="not_found", status_code=404)

class AuthenticationError(AgentForgeException):
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, code="authentication_error", status_code=401)

class PermissionDeniedError(AgentForgeException):
    def __init__(self, message: str = "Permission denied"):
        super().__init__(message, code="permission_denied", status_code=403)

class ConflictError(AgentForgeException):
    def __init__(self, message: str = "Conflict"):
        super().__init__(message, code="conflict", status_code=409)

class DatabaseError(AgentForgeException):
    def __init__(self, message: str = "Database unavailable"):
        super().__init__(message, code="database_error", status_code=503)