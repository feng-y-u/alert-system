"""可靠性回归测试。

覆盖 docs/tech/14-评估与改进.md 的 P0-1：broker（Redis）不可用时，
日志上报接口仍须正常返回，且日志确实落库。
"""

from datetime import datetime, timezone

from app.core.config import settings
from app.models.login_log import LoginLog
from app.schemas.login_log import LoginLogCreate
from app.services.logs import create_log


def _broker_down(*args, **kwargs):
    """模拟 broker 不可用（kombu 会抛 OperationalError 之类的异常）。"""
    raise OSError("broker unavailable")


def test_create_log_survives_broker_failure(monkeypatch, db):
    """投递检测任务失败时，service 层仍返回已落库的日志。"""
    monkeypatch.setattr("app.tasks.detection.detect_anomaly_for_log.delay", _broker_down)

    log = create_log(
        db,
        LoginLogCreate(
            username="resilient_user",
            login_time=datetime.now(timezone.utc),
            ip_address="10.0.0.1",
            user_agent="pytest",
            login_status="success",
        ),
    )

    assert log.id is not None
    stored = db.query(LoginLog).filter(LoginLog.id == log.id).first()
    assert stored is not None
    assert stored.username == "resilient_user"


def test_post_log_returns_201_when_broker_down(client, monkeypatch):
    """broker 不可用时 POST /api/logs 仍返回 201（此前会长时间阻塞）。"""
    monkeypatch.setattr("app.tasks.detection.detect_anomaly_for_log.delay", _broker_down)

    resp = client.post(
        "/api/logs",
        json={
            "username": "resilient_student",
            "login_time": datetime.now(timezone.utc).isoformat(),
            "ip_address": "10.0.0.2",
            "user_agent": "pytest",
            "login_status": "success",
        },
        headers={"X-API-Key": settings.API_KEY},
    )

    assert resp.status_code == 201
    assert resp.json()["username"] == "resilient_student"
