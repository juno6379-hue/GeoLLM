class MarinePlatformError(Exception):
    """Base exception for Marine Geospatial Intelligence Platform"""
    def __init__(self, message: str, code: str = "INTERNAL_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)

class DataAccessDeniedError(MarinePlatformError):
    def __init__(self, message: str = "해당 데이터셋에 접근할 권한이 없습니다."):
        super().__init__(message, code="DATA_ACCESS_DENIED")

class ToolExecutionError(MarinePlatformError):
    def __init__(self, message: str = "Tool 실행 중 오류가 발생했습니다."):
        super().__init__(message, code="TOOL_EXECUTION_ERROR")

class ValidationFailedError(MarinePlatformError):
    def __init__(self, message: str = "결과 검증에 실패했습니다."):
        super().__init__(message, code="VALIDATION_FAILED")

class RegistryNotFoundError(MarinePlatformError):
    def __init__(self, message: str = "레지스트리에서 항목을 찾을 수 없습니다."):
        super().__init__(message, code="REGISTRY_NOT_FOUND")
