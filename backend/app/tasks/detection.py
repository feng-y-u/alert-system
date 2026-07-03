"""Celery 异步任务：异常检测"""

from app.tasks import celery_app


@celery_app.task
def run_anomaly_detection() -> str:
    """执行周期性异常检测（待第 4 周实现检测逻辑）"""
    # TODO: 第 4 周集成 Pandas 异常检测
    return "Anomaly detection run completed (noop)"