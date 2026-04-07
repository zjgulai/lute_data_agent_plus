"""数据服务异常定义."""

from __future__ import annotations


class DataServiceError(Exception):
    """数据服务基础异常."""

    def __init__(self, message: str, error_code: str = "DATA_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

    def to_dict(self) -> dict[str, str]:
        """转换为字典格式."""
        return {
            "error_code": self.error_code,
            "message": self.message,
        }


class DataMissingError(DataServiceError):
    """数据缺失异常.

    当必需的字段缺失或数据为空时抛出。
    """

    def __init__(
        self,
        message: str,
        missing_fields: Optional[list[str]] = None,
        available_fields: Optional[list[str]] = None,
    ):
        super().__init__(message, error_code="DATA_MISSING")
        self.missing_fields = missing_fields or []
        self.available_fields = available_fields or []

    def to_dict(self) -> dict[str, any]:
        """转换为字典格式."""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "missing_fields": self.missing_fields,
            "available_fields": self.available_fields,
        }


class DataFormatError(DataServiceError):
    """数据格式错误异常."""

    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(message, error_code="DATA_FORMAT_ERROR")
        self.field = field

    def to_dict(self) -> dict[str, any]:
        result = super().to_dict()
        if self.field:
            result["field"] = self.field
        return result
