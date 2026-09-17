"""应用配置与启动期自检。

设计约定：

- **唯一事实来源**：所有配置集中在 ``settings``（pydantic-settings），其它模块只读它；
- **启动期安全自检**：敏感项仍是示例占位值时，生产环境拒绝启动、开发环境强警告
  （``docs/tech/14-评估与改进.md`` P0-2 / ``10-安全分析.md`` SEC-02）；
- **时间口径统一**：数据库统一存 UTC，对外展示的自然日按 ``BUSINESS_TIMEZONE`` 切分，
  Celery 调度使用同一时区（``tasks/__init__.py``），消除此前 UTC/Asia-Shanghai 混用
  （``docs/tech/14-评估与改进.md`` P1-8）。
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import List
from zoneinfo import ZoneInfo

from pydantic import ConfigDict
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)

#: 取值中出现任一片段，即认为该配置项仍是示例/占位值
INSECURE_MARKERS = (
    "change-me",
    "change-in-production",
    "your-secret-key",
    "dev-api-key",
    "changethis",
)

#: 需要做占位值检查的敏感配置项
SENSITIVE_KEYS = ("SECRET_KEY", "API_KEY")


class Settings(BaseSettings):
    PROJECT_NAME: str = "校园账号异常登录监测平台"
    VERSION: str = "0.1.0"
    API_V1_PREFIX: str = "/api"

    #: development | production；production 下使用占位密钥会拒绝启动
    ENVIRONMENT: str = "development"
    #: 业务时区（统计自然日与 Celery 调度共用；数据库始终存 UTC）
    BUSINESS_TIMEZONE: str = "Asia/Shanghai"

    DATABASE_URL: str = "mysql+pymysql://campus_user:campus123@localhost:8881/campus_monitor"
    REDIS_URL: str = "redis://localhost:8880/0"

    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    ALGORITHM: str = "HS256"
    API_KEY: str = "dev-api-key-change-in-production"

    #: 登录失败限流：同一（用户名 + IP）在窗口内最多失败次数
    LOGIN_MAX_FAILURES: int = 5
    LOGIN_FAILURE_WINDOW_SECONDS: int = 900

    EMAIL_HOST: str = "smtp.example.com"
    EMAIL_PORT: int = 465
    EMAIL_USER: str = ""
    EMAIL_PASSWORD: str = ""
    ALERT_EMAIL_FROM: str = "campus-monitor@localhost"

    model_config = ConfigDict(env_file=".env", case_sensitive=True)


settings = Settings()


# ─────────────────────────── 日志 ───────────────────────────


def configure_logging() -> None:
    """配置最小可用日志（输出到 stdout）。

    已有 root handler 时不重复配置（例如 uvicorn 或 pytest 已配置）。
    """
    if logging.getLogger().handlers:
        return
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-5s [%(name)s] %(message)s",
    )


# ─────────────────── 启动期安全自检与配置输出 ───────────────────


def insecure_defaults() -> List[str]:
    """返回仍在使用占位默认值的敏感配置项名（**只返回名称，不返回取值**）。"""
    found: List[str] = []
    for name in SENSITIVE_KEYS:
        value = str(getattr(settings, name, "") or "").lower()
        if any(marker in value for marker in INSECURE_MARKERS):
            found.append(name)
    return found


def is_production() -> bool:
    """是否运行在生产环境。"""
    return settings.ENVIRONMENT.strip().lower() in {"production", "prod"}


def assert_secure_config() -> None:
    """启动期校验敏感配置。

    生产环境命中占位值 → 抛 ``RuntimeError`` 拒绝启动；
    开发环境 → 打印醒目 WARNING（不阻断，避免影响本地开发与测试）。
    """
    insecure = insecure_defaults()
    if not insecure:
        return

    joined = "、".join(insecure)
    if is_production():
        raise RuntimeError(
            f"检测到仍在使用示例占位值的敏感配置：{joined}。"
            "当前 ENVIRONMENT=production，已拒绝启动；"
            "请先设置强随机值（见 docs/tech/10-安全分析.md SEC-02）。"
        )
    logger.warning(
        "安全警告：%s 仍在使用示例占位值，仅可用于本地开发；"
        "部署到任何可访问的环境前必须替换为强随机值"
        "（见 docs/tech/10-安全分析.md SEC-02）。",
        joined,
    )


def _mask_url(url: str) -> str:
    """抹掉连接串中的凭据，避免写进日志。"""
    if "://" not in url or "@" not in url:
        return url
    scheme, rest = url.split("://", 1)
    return f"{scheme}://***@{rest.split('@', 1)[1]}"


def describe_effective_config() -> str:
    """生成不含任何密钥取值的有效配置摘要，供启动日志打印（P1-8）。"""
    return (
        f"env={settings.ENVIRONMENT} "
        f"api_prefix={settings.API_V1_PREFIX} "
        f"database={_mask_url(settings.DATABASE_URL)} "
        f"redis={_mask_url(settings.REDIS_URL)} "
        f"token_expire_minutes={settings.ACCESS_TOKEN_EXPIRE_MINUTES} "
        f"business_timezone={settings.BUSINESS_TIMEZONE} "
        f"email_configured={'yes' if settings.EMAIL_USER else 'no'} "
        f"insecure_defaults={insecure_defaults() or 'none'}"
    )


def log_startup_config() -> None:
    """打印有效配置摘要。"""
    logger.info("effective config: %s", describe_effective_config())


# ─────────────────────── 业务时区工具 ───────────────────────


def business_tz() -> ZoneInfo:
    """业务时区对象。"""
    return ZoneInfo(settings.BUSINESS_TIMEZONE)


def business_now() -> datetime:
    """当前业务时区时间（带时区信息）。"""
    return datetime.now(business_tz())


def business_day_start(moment: datetime | None = None) -> datetime:
    """给定时刻所在业务自然日的 00:00（返回业务时区 aware 时间）。"""
    base = moment or business_now()
    return base.astimezone(business_tz()).replace(
        hour=0, minute=0, second=0, microsecond=0
    )


def to_utc_naive(moment: datetime) -> datetime:
    """业务时区时刻 → UTC naive（与数据库 DATETIME 列的存储口径一致）。"""
    return moment.astimezone(timezone.utc).replace(tzinfo=None)


def business_day_start_utc_naive(moment: datetime | None = None) -> datetime:
    """业务自然日 00:00 对应的 UTC naive 时间。"""
    return to_utc_naive(business_day_start(moment))


def business_utc_offset_hours(moment: datetime | None = None) -> int:
    """业务时区相对 UTC 的整点偏移（用于 SQL 侧日期折算）。"""
    offset = business_day_start(moment).utcoffset() or timedelta()
    return int(offset.total_seconds() // 3600)
