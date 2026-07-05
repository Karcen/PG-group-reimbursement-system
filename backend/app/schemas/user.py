"""
用户相关 Pydantic Schema
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.user import UserRole


# ─── 基础字段 ──────────────────────────────────────────────────────────────

class UserBase(BaseModel):
    username: str = Field(min_length=2, max_length=64, description="用户名")
    email: EmailStr = Field(description="邮箱")
    full_name: str = Field(default="", max_length=64, description="真实姓名")
    student_id: Optional[str] = Field(default=None, max_length=32, description="学号/工号")
    department: Optional[str] = Field(default=None, max_length=64, description="所属部门/课题组")
    role: UserRole = Field(default=UserRole.STUDENT, description="用户角色")


# ─── 创建请求 ──────────────────────────────────────────────────────────────

class UserCreate(UserBase):
    """创建用户请求（管理员使用）"""
    password: str = Field(min_length=8, max_length=64, description="初始密码")

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """密码至少包含大写字母、小写字母和数字"""
        if not any(c.isupper() for c in v):
            raise ValueError("密码必须包含至少一个大写字母")
        if not any(c.islower() for c in v):
            raise ValueError("密码必须包含至少一个小写字母")
        if not any(c.isdigit() for c in v):
            raise ValueError("密码必须包含至少一个数字")
        return v


# ─── 更新请求 ──────────────────────────────────────────────────────────────

class UserUpdate(BaseModel):
    """更新用户信息请求（用户自己更新个人资料）"""
    full_name: Optional[str] = Field(default=None, max_length=64)
    department: Optional[str] = Field(default=None, max_length=64)
    avatar_url: Optional[str] = Field(default=None, max_length=256)


class UserAdminUpdate(UserUpdate):
    """管理员更新用户信息（可修改角色和启用状态）"""
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    email: Optional[EmailStr] = None


class PasswordChange(BaseModel):
    """修改密码请求"""
    old_password: str = Field(description="当前密码")
    new_password: str = Field(min_length=8, max_length=64, description="新密码")

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("密码必须包含至少一个大写字母")
        if not any(c.islower() for c in v):
            raise ValueError("密码必须包含至少一个小写字母")
        if not any(c.isdigit() for c in v):
            raise ValueError("密码必须包含至少一个数字")
        return v


class PasswordReset(BaseModel):
    """管理员重置密码请求"""
    new_password: str = Field(min_length=8, max_length=64)


# ─── 响应 Schema ───────────────────────────────────────────────────────────

class UserOut(BaseModel):
    """用户信息响应（不含密码）"""
    id: int
    username: str
    email: str
    full_name: str
    student_id: Optional[str]
    department: Optional[str]
    role: UserRole
    is_active: bool
    avatar_url: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class UserBrief(BaseModel):
    """简化用户信息（用于列表、关联显示）"""
    id: int
    username: str
    full_name: str
    role: UserRole

    model_config = {"from_attributes": True}


# ─── 认证 Schema ───────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    """登录请求"""
    username: str = Field(description="用户名")
    password: str = Field(description="密码")


class TokenResponse(BaseModel):
    """登录成功后返回的 Token"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Access Token 有效秒数")
    user: UserOut
