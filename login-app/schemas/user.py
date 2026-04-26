"""
Pydantic 模型
用于请求验证和数据转换
"""
from pydantic import BaseModel, EmailStr, Field, field_validator


class LoginRequest(BaseModel):
    """登录请求模型"""
    identifier: str = Field(..., min_length=1, description="用户名或邮箱")
    password: str = Field(..., min_length=1, description="密码")


class RegisterRequest(BaseModel):
    """用户注册请求模型"""
    email: EmailStr = Field(..., description="邮箱")
    password: str = Field(..., min_length=8, description="密码（至少8个字符）")
    username: str = Field(..., min_length=2, max_length=50, description="用户名")

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """验证密码强度"""
        if not any(c.isupper() for c in v):
            raise ValueError("密码必须包含至少一个大写字母")
        if not any(c.islower() for c in v):
            raise ValueError("密码必须包含至少一个小写字母")
        if not any(c.isdigit() for c in v):
            raise ValueError("密码必须包含至少一个数字")
        return v


class UserResponse(BaseModel):
    """用户响应模型"""
    id: str
    email: str
    username: str


class LoginResponse(BaseModel):
    """登录响应模型"""
    success: bool
    user: UserResponse | None = None
    redirect_to: str | None = None


class RegisterResponse(BaseModel):
    """注册响应模型"""
    success: bool
    user: UserResponse | None = None
    message: str | None = None


class ErrorResponse(BaseModel):
    """错误响应模型"""
    error: str
    code: str
