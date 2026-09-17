from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.vocab import MIN_PASSWORD_LENGTH


class UserCreate(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    email: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=MIN_PASSWORD_LENGTH, max_length=128)


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    is_active: bool
    must_change_password: bool = False
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    #: True 时管理端必须先调用 /api/auth/change-password 才能使用其它接口
    must_change_password: bool = False


class PasswordChange(BaseModel):
    """修改自己的密码（初始密码场景下唯一可用的写接口）。"""

    old_password: str
    new_password: str = Field(min_length=MIN_PASSWORD_LENGTH, max_length=128)
