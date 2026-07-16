from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.health import router as health_router
from app.api.auth import router as auth_router
from app.api.stats import router as stats_router
from app.api.logs import router as logs_router
from app.api.alerts import router as alerts_router
from app.api.notifications import router as notifications_router
from app.api.settings import router as settings_router

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
