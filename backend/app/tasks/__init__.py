from celery import Celery

from app.core.config import assert_secure_config, settings

# Worker / Beat 进程同样做启动期自检（生产环境命中占位密钥则拒绝启动）
assert_secure_config()

celery_app = Celery(
    "campus_monitor",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.email", "app.tasks.detection"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    # 与统计接口共用同一业务时区，避免 UTC 与 Asia/Shanghai 混用
    # （见 docs/tech/07-配置与依赖.md §15.3 配置漂移）
    timezone=settings.BUSINESS_TIMEZONE,
    enable_utc=True,
    # 本项目的任务返回值只用于日志排查，不消费结果。
    # 关闭结果后，发布任务时不会启动 result backend 的 pubsub 消费端——
    # 那正是 Redis 不可用时 POST /api/logs 被无限重试卡住的根因
    # （见 docs/tech/11-性能分析.md PERF-00）。
    task_ignore_result=True,
    # 为 broker / result backend 设置短超时与有限重试，
    # 保证 Redis 不可用时快速失败，而不是长时间占住请求线程。
    broker_transport_options={
        "socket_connect_timeout": 2,
        "socket_timeout": 2,
        "max_retries": 2,
        "interval_start": 0,
        "interval_step": 0.2,
        "interval_max": 0.5,
    },
    result_backend_transport_options={
        "socket_connect_timeout": 2,
        "socket_timeout": 2,
    },
    redis_socket_connect_timeout=2,
    redis_socket_timeout=2,
    task_publish_retry_policy={
        "max_retries": 2,
        "interval_start": 0,
        "interval_step": 0.2,
        "interval_max": 0.5,
    },
    # Beat 定时任务配置
    beat_schedule={
        "anomaly-detection-every-hour": {
            "task": "app.tasks.detection.run_anomaly_detection",
            "schedule": 3600.0,  # 每小时运行一次（秒）
        },
    },
)
