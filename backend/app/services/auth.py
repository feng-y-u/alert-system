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


#: 新密码最小长度（与 schemas 校验同源，定义在 core/vocab.py）
from app.core.vocab import MIN_PASSWORD_LENGTH


class PasswordChangeError(Exception):
    """修改密码失败时抛出"""


def change_password(
    db: Session, user: User, old_password: str, new_password: str
) -> User:
    """修改密码：校验原密码与强度，并清除「首次登录必须改密」标记。"""
    if not verify_password(old_password, user.hashed_password):
        raise PasswordChangeError("原密码错误")
    if len(new_password) < MIN_PASSWORD_LENGTH:
        raise PasswordChangeError(f"新密码长度至少 {MIN_PASSWORD_LENGTH} 位")
    if new_password == old_password:
        raise PasswordChangeError("新密码不能与原密码相同")

    user.hashed_password = get_password_hash(new_password)
    user.must_change_password = False
    db.commit()
    db.refresh(user)
    return user