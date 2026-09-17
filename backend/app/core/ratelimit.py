"""登录失败限流（Redis 固定窗口计数）。

设计取舍：Redis 不可用时**放行并告警**（fail-open）。限流是加固手段，
不应因缓存故障把管理员锁在门外——这与「Redis 故障不得放大为全站故障」
（``docs/tech/11-性能分析.md`` PERF-00）保持一致。
"""

import logging
import time

from app.core.config import settings

logger = logging.getLogger(__name__)

_KEY_PREFIX = "login_failures"

#: Redis 不可用后的熔断时长（秒）：期间直接放行，不再每次登录都付连接超时
UNAVAILABLE_COOLDOWN_SECONDS = 30
_unavailable_until = 0.0


def _mark_unavailable() -> None:
    global _unavailable_until
    _unavailable_until = time.monotonic() + UNAVAILABLE_COOLDOWN_SECONDS


def _skip_fast() -> bool:
    """熔断期内直接返回，避免登录路径反复等待连接超时。"""
    return time.monotonic() < _unavailable_until


def reset_circuit_breaker() -> None:
    """清空熔断状态（测试与运维手动恢复用）。"""
    global _unavailable_until
    _unavailable_until = 0.0

#: 提示用：登录失败计数所用的键前缀（运维排查用）
def key_prefix() -> str:
    return _KEY_PREFIX


def _client():
    import redis

    # 限流只是加固手段：超时必须短，不能让登录接口被慢 Redis 拖住
    return redis.from_url(
        settings.REDIS_URL, socket_connect_timeout=0.5, socket_timeout=0.5
    )


def _key(username: str, ip: str | None) -> str:
    return f"{_KEY_PREFIX}:{(username or '').strip().lower()}:{ip or 'unknown'}"


def _limit() -> int:
    return max(1, int(settings.LOGIN_MAX_FAILURES))


def _window() -> int:
    return max(1, int(settings.LOGIN_FAILURE_WINDOW_SECONDS))


def is_blocked(username: str, ip: str | None) -> tuple[bool, int]:
    """判断是否已被限流。

    Returns:
        ``(是否拦截, 建议重试秒数)``；Redis 不可用时返回 ``(False, 0)``（放行）。
    """
    key = _key(username, ip)
    if _skip_fast():
        return False, 0
    try:
        client = _client()
        try:
            count = int(client.get(key) or 0)
            if count < _limit():
                return False, 0
            ttl = int(client.ttl(key) or _window())
            return True, max(ttl, 1)
        finally:
            client.close()
    except Exception:
        _mark_unavailable()
        logger.warning("登录限流检查已跳过（Redis 不可用，fail-open）", exc_info=True)
        return False, 0


def register_failure(username: str, ip: str | None) -> int:
    """记录一次登录失败，返回当前窗口内累计失败次数（Redis 不可用时返回 0）。"""
    key = _key(username, ip)
    if _skip_fast():
        return 0
    try:
        client = _client()
        try:
            pipe = client.pipeline()
            pipe.incr(key)
            pipe.expire(key, _window())
            return int(pipe.execute()[0])
        finally:
            client.close()
    except Exception:
        _mark_unavailable()
        logger.warning("登录失败计数未记录（Redis 不可用）", exc_info=True)
        return 0


def reset(username: str, ip: str | None) -> None:
    """登录成功后清除失败计数。"""
    if _skip_fast():
        return
    try:
        client = _client()
        try:
            client.delete(_key(username, ip))
        finally:
            client.close()
    except Exception:
        _mark_unavailable()
        logger.warning("登录失败计数未清除（Redis 不可用）", exc_info=True)
