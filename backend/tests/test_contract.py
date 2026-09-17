"""契约测试：词表归一化与状态校验（对应 docs/tech/14-评估与改进.md P1-3）。"""

from datetime import datetime, timezone

from app.core.security import create_access_token, get_password_hash
from app.core.vocab import LOGIN_STATUS_FAILURE, LOGIN_STATUS_SUCCESS
from app.models.alert import Alert
from app.models.login_log import LoginLog
from app.models.user import User


def _admin_headers(db) -> dict:
    user = User(
        username="admin",
        email="admin@test.com",
        hashed_password=get_password_hash("admin123"),
        role="admin",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"Authorization": f"Bearer {create_access_token(data={'sub': str(user.id)})}"}


def _post_log(client, status_value: str, username: str = "vocab_user"):
    return client.post(
        "/api/logs",
        json={
            "username": username,
            "login_time": datetime.now(timezone.utc).isoformat(),
            "ip_address": "10.0.0.9",
            "user_agent": "pytest",
            "login_status": status_value,
        },
        headers={"X-API-Key": "dev-api-key-change-in-production"},
    )


def test_legacy_failed_is_normalized_to_failure(client, db):
    """monitored-app 历史上报的 failed 必须入库为 failure，否则按失败筛不出来。"""
    resp = _post_log(client, "failed")

    assert resp.status_code == 201
    assert resp.json()["login_status"] == LOGIN_STATUS_FAILURE

    stored = db.query(LoginLog).filter(LoginLog.username == "vocab_user").one()
    assert stored.login_status == LOGIN_STATUS_FAILURE


def test_success_passes_through(client, db):
    resp = _post_log(client, "success", username="vocab_ok")

    assert resp.status_code == 201
    assert resp.json()["login_status"] == LOGIN_STATUS_SUCCESS


def test_unknown_login_status_is_rejected(client, db):
    resp = _post_log(client, "locked_out", username="vocab_bad")

    assert resp.status_code == 422


def test_failed_status_is_queryable_after_normalization(client, db):
    """归一化后，按 failure 筛选应能查到该条日志。"""
    headers = _admin_headers(db)
    _post_log(client, "failed", username="vocab_query")

    resp = client.get("/api/logs?login_status=failure&username=vocab_query", headers=headers)

    assert resp.status_code == 200
    assert resp.json()["total"] == 1


def test_alert_status_rejects_unknown_value(client, db):
    headers = _admin_headers(db)
    alert = Alert(
        username="vocab_alert",
        alert_type="frequency",
        alert_message="x",
        severity="medium",
        status="pending",
    )
    db.add(alert)
    db.commit()

    resp = client.put(f"/api/alerts/{alert.id}", json={"status": "done"}, headers=headers)

    assert resp.status_code == 422


def test_sse_stream_rejects_invalid_token(client, db):
    """SSE 鉴权失败必须立即 401，而不是建立一条永不产出的流。"""
    resp = client.get("/api/notifications/stream?token=not-a-real-token")

    assert resp.status_code == 401
