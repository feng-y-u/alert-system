import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import (
    assert_secure_config,
    configure_logging,
    log_startup_config,
    settings,
)
from app.api.health import router as health_router
from app.api.auth import router as auth_router
from app.api.stats import router as stats_router
from app.api.logs import router as logs_router
from app.api.alerts import router as alerts_router
from app.api.notifications import router as notifications_router
from app.api.settings import router as settings_router
from app.api.audit import router as audit_router

# 启动期自检：先配置日志，便于把安全警告与有效配置打印出来
# （生产环境命中占位密钥会在此直接拒绝启动，见 docs/tech/10-安全分析.md SEC-02）
configure_logging()
assert_secure_config()
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="安全审计与日志分析系统API",
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix=settings.API_V1_PREFIX, tags=["健康检查"])
app.include_router(auth_router, prefix=settings.API_V1_PREFIX, tags=["认证"])
app.include_router(stats_router, prefix=settings.API_V1_PREFIX, tags=["统计"])
app.include_router(logs_router, prefix=settings.API_V1_PREFIX, tags=["日志"])
app.include_router(alerts_router, prefix=settings.API_V1_PREFIX, tags=["告警"])
app.include_router(notifications_router, prefix=settings.API_V1_PREFIX, tags=["实时通知"])
app.include_router(settings_router, prefix=settings.API_V1_PREFIX, tags=["设置"])
app.include_router(audit_router, prefix=settings.API_V1_PREFIX, tags=["审计"])

log_startup_config()
