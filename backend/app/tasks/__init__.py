from celery import Celery

from app.core.config import settings
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
    timezone="Asia/Shanghai",
    enable_utc=True,
    # Beat 定时任务配置
    beat_schedule={
        "anomaly-detection-every-hour": {
            "task": "app.tasks.detection.run_anomaly_detection",
            "schedule": 3600.0,  # 每小时运行一次（秒）
        },
    },
)