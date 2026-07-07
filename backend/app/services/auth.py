"""认证业务逻辑"""

from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.models.user import User


class AuthenticationError(Exception):
    """认证失败时抛出的异常"""
    pass


def authenticate_user(db: Session, username: str, password: str) -> User:
    """验证用户凭据，成功返回 User，失败抛出 AuthenticationError"""
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        raise AuthenticationError("用户名或密码错误")
    if not user.is_active:
        raise AuthenticationError("用户已被禁用")

    return user


def create_admin_user(db: Session, username: str, email: str, password: str) -> User:
    """创建新管理员，用户名或邮箱重复时抛出 ValueError"""
    if db.query(User).filter(User.username == username).first():
        raise ValueError("用户名已存在")
    if db.query(User).filter(User.email == email).first():
        raise ValueError("邮箱已被使用")

    user = User(
        username=username,
        email=email,
        hashed_password=get_password_hash(password),
        role="admin",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user_by_id(db: Session, user_id: int) -> User | None:
    """根据 ID 获取用户"""
    return db.query(User).filter(User.id == user_id).first()