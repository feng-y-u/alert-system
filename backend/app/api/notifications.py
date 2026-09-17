"""SSE 实时告警推送。

实现要点（对应 docs/tech/14-评估与改进.md P1-2）：

- 鉴权使用**独立短会话**，不再声明 ``Depends(get_db)``。请求级会话会一直持有到
  客户端断开，约 15 个并发连接即可耗尽默认连接池；
- Redis 订阅失败直接返回 503，而不是让客户端挂在一个永不产出的流上；
- 建立/异常/关闭都写日志，便于排查实时推送故障。
"""

import logging

from fastapi import APIRouter, HTTPException, Query
from starlette.responses import StreamingResponse

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.security import decode_access_token
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()

ALERT_CHANNEL = "alerts"


def _get_user_from_token(token: str, db) -> User:
    """解析 token 并载入用户（与 core/deps.py 的校验语义保持一致）。"""
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Token 无效或已过期")

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Token 中缺少用户信息")

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise HTTPException(status_code=401, detail="用户不存在")
    if not user.is_active:
        raise HTTPException(status_code=401, detail="用户已被禁用")

    return user


@router.get("/notifications/stream")
async def stream_notifications(
    token: str = Query(..., description="JWT Token"),
):
    """建立 SSE 流，把 Redis 频道 ``alerts`` 上的告警事件推给管理端。"""
    db = SessionLocal()
    try:
        user = _get_user_from_token(token, db)
    finally:
        db.close()

    import redis.asyncio as aioredis

    r = aioredis.from_url(settings.REDIS_URL)
    pubsub = r.pubsub()
    try:
        await pubsub.subscribe(ALERT_CHANNEL)
    except Exception:
        logger.exception("SSE: 订阅 Redis 频道 %s 失败", ALERT_CHANNEL)
        try:
            await r.close()
        except Exception:  # pragma: no cover - 清理失败无需再报
            pass
        raise HTTPException(status_code=503, detail="实时推送服务暂不可用")

    logger.info("SSE 连接已建立：user=%s", user.username)

    async def event_generator():
        try:
            while True:
                message = await pubsub.get_message(
                    timeout=1.0, ignore_subscribe_messages=True
                )
                if message and message["type"] == "message":
                    yield f"data: {message['data'].decode()}\n\n"
                else:
                    yield f": heartbeat\n\n"
        except Exception:
            logger.exception("SSE 流异常终止：user=%s", user.username)
        finally:
            await pubsub.unsubscribe(ALERT_CHANNEL)
            await pubsub.close()
            await r.close()
            logger.info("SSE 连接已关闭：user=%s", user.username)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
