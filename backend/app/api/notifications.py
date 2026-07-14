from fastapi import APIRouter, Depends, HTTPException, Query
from starlette.responses import StreamingResponse
from sqlalchemy.orm import Session

import redis
from app.core.config import settings
from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User

router = APIRouter()


def _get_user_from_token(token: str, db: Session) -> User:
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
    db: Session = Depends(get_db),
):
    _get_user_from_token(token, db)

    r = redis.from_url(settings.REDIS_URL)
    pubsub = r.pubsub()
    pubsub.subscribe("alerts")

    async def event_generator():
        try:
            while True:
                message = pubsub.get_message(timeout=1.0)
                if message and message["type"] == "message":
                    yield f"data: {message['data']}\n\n"
                else:
                    yield f": heartbeat\n\n"
        except Exception:
            pass
        finally:
            pubsub.unsubscribe("alerts")
            pubsub.close()

    return StreamingResponse(event_generator(), media_type="text/event-stream")
