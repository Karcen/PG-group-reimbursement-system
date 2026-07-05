"""
公共 Schema 定义
统一 API 响应格式，所有接口返回值均包装在 ApiResponse 中。
"""

from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """
    统一 API 响应格式
    示例：{"success": true, "code": "OK", "message": "操作成功", "data": {...}}
    """
    success: bool = True
    code: str = "OK"
    message: str = "操作成功"
    data: Optional[T] = None

    @classmethod
    def ok(cls, data: T = None, message: str = "操作成功") -> "ApiResponse[T]":
        return cls(success=True, code="OK", message=message, data=data)

    @classmethod
    def fail(cls, message: str, code: str = "ERROR", data=None) -> "ApiResponse":
        return cls(success=False, code=code, message=message, data=data)


class PaginationParams(BaseModel):
    """分页请求参数"""
    page: int = Field(default=1, ge=1, description="页码（从1开始）")
    page_size: int = Field(default=20, ge=1, le=100, description="每页条数（最大100）")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class PaginatedData(BaseModel, Generic[T]):
    """分页响应数据"""
    items: list[T]
    total: int = Field(description="总条数")
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页条数")
    total_pages: int = Field(description="总页数")

    @classmethod
    def create(cls, items: list[T], total: int, page: int, page_size: int) -> "PaginatedData[T]":
        import math
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=max(1, math.ceil(total / page_size)) if total > 0 else 1,
        )
