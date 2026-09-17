import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core import ratelimit
from app.core.database import get_db
from app.core.deps import get_current_active_user, get_current_user
from app.core.security import create_access_token
from app.models.user import User
from app.schemas.user import PasswordChange, Token, UserCreate, UserLogin, UserResponse
from app.services.audit import (
    AUDIT_LOGIN_FAILED,
    AUDIT_LOGIN_SUCCESS,
    AUDIT_PASSWORD_CHANGED,
    AUDIT_USER_CREATED,
    record,
)
from app.services.auth import (
    AuthenticationError,
    PasswordChangeError,
    authenticate_user,
    change_password,
    create_admin_user,
)

router = APIRouter()
logger = logging.getLogger(__name__)


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


@router.post("/auth/login", response_model=Token)
def login(payload: UserLogin, request: Request, db: Session = Depends(get_db)):
    """管理员登录，返回 JWT token。

    带登录失败限流（P1-6）：同一「用户名 + 来源 IP」在窗口内失败达上限则返回 429；
    Redis 不可用时限流自动放行（fail-open）。
    """
    ip = _client_ip(request)

    blocked, retry_after = ratelimit.is_blocked(payload.username, ip)
    if blocked:
        logger.warning("登录被限流：username=%s ip=%s", payload.username, ip)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"登录失败次数过多，请 {retry_after} 秒后重试",
            headers={"Retry-After": str(retry_after)},
        )

    try:
        user = authenticate_user(db, payload.username, payload.password)
    except AuthenticationError as e:
        failures = ratelimit.register_failure(payload.username, ip)
        record(
            db,
            AUDIT_LOGIN_FAILED,
            actor=None,
            target=payload.username,
            detail=f"来源 IP={ip}，本次窗口内失败 {failures} 次：{e}",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )

    ratelimit.reset(payload.username, ip)
    record(
        db,
        AUDIT_LOGIN_SUCCESS,
        actor=user,
        target=user.username,
        detail=f"来源 IP={ip}",
    )

    token = create_access_token(data={"sub": str(user.id)})
    return Token(
        access_token=token,
        must_change_password=bool(user.must_change_password),
    )


@router.post("/auth/change-password", response_model=Token)
def change_own_password(
    payload: PasswordChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """修改**自己**的密码。

    这是初始口令未修改时唯一可用的写接口（其它接口会被 ``get_current_active_user``
    以 403 拦住），因此这里使用 ``get_current_user`` 并在函数内自行校验启用状态。
    成功后返回新 token，``must_change_password`` 置为 False。
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="用户已被禁用"
        )

    try:
        user = change_password(db, current_user, payload.old_password, payload.new_password)
    except PasswordChangeError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    record(
        db,
        AUDIT_PASSWORD_CHANGED,
        actor=user,
        target=user.username,
        detail="用户自行修改密码",
    )

    return Token(
        access_token=create_access_token(data={"sub": str(user.id)}),
        must_change_password=False,
    )


@router.post("/auth/register", response_model=UserResponse)
def register(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """创建新管理员（仅已登录管理员可调用）"""
    try:
        user = create_admin_user(db, payload.username, payload.email, payload.password)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    record(
        db,
        AUDIT_USER_CREATED,
        actor=current_user,
        target=user.username,
        detail=f"由 {current_user.username} 创建管理员账号",
    )
    return user


@router.get("/auth/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_active_user)):
    """获取当前登录用户信息"""
    return current_user
