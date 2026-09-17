"""治理类回归测试。

覆盖 docs/tech/14-评估与改进.md：

- **P1-4**：销毁接口的确认参数、软删除、审计日志、告警状态变更语义；
- **P1-6**：登录失败限流（含 Redis 不可用的 fail-open 与熔断）、初始密码强制修改。
"""

from datetime import datetime, timezone

from app.core import ratelimit
from app.core.security import create_access_token, get_password_hash
from app.models.alert import Alert
from app.models.audit_log import AuditLog
from app.models.login_log import LoginLog
from app.models.user import User
from app.services.audit import (
    AUDIT_ALERT_STATUS_CHANGED,
    AUDIT_ALERTS_CLEARED,
    AUDIT_LOGIN_FAILED,
    AUDIT_LOGIN_SUCCESS,
    AUDIT_LOGS_CLEARED,
    AUDIT_PASSWORD_CHANGED,
)


def _make_admin(db, username="admin", password="admin123", must_change=False) -> dict:
    user = User(
        username=username,
        email=f"{username}@test.com",
        hashed_password=get_password_hash(password),
        role="admin",
        is_active=True,
        must_change_password=must_change,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"Authorization": f"Bearer {create_access_token(data={'sub': str(user.id)})}"}


def _now():
    return datetime.now(timezone.utc)


# ─────────────── P1-4：确认参数 + 软删除 + 审计 ───────────────


def test_clear_logs_requires_confirmation(client, db):
    headers = _make_admin(db)

    resp = client.delete("/api/logs", headers=headers)

    assert resp.status_code == 409
    assert "confirm=true" in resp.json()["detail"]


def test_clear_logs_is_soft_delete_and_audited(client, db):
    headers = _make_admin(db)
    db.add(
        LoginLog(
            username="soft_del_user",
            login_time=_now(),
            ip_address="10.1.1.1",
            login_status="success",
        )
    )
    db.commit()

    resp = client.delete("/api/logs?confirm=true", headers=headers)

    assert resp.status_code == 200
    assert resp.json() == {"deleted": 1, "soft_deleted": True}

    db.expire_all()
    row = db.query(LoginLog).filter(LoginLog.username == "soft_del_user").one()
    assert row.deleted_at is not None, "数据必须保留（软删除），而不是物理删除"

    assert client.get("/api/logs", headers=headers).json()["total"] == 0
    assert client.get("/api/stats", headers=headers).json()["todayLogins"] == 0

    entry = db.query(AuditLog).filter(AuditLog.action == AUDIT_LOGS_CLEARED).one()
    assert entry.actor_username == "admin"
    assert entry.affected_rows == 1


def test_clear_alerts_requires_confirmation_and_is_soft_delete(client, db):
    headers = _make_admin(db)
    db.add(
        Alert(
            username="soft_del_alert",
            alert_type="frequency",
            alert_message="m",
            severity="high",
            status="resolved",
        )
    )
    db.commit()

    assert client.delete("/api/alerts?scope=all", headers=headers).status_code == 409

    resp = client.delete("/api/alerts?scope=all&confirm=true", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["soft_deleted"] is True

    db.expire_all()
    assert (
        db.query(Alert).filter(Alert.username == "soft_del_alert").one().deleted_at
        is not None
    )
    assert client.get("/api/alerts", headers=headers).json()["total"] == 0
    assert (
        db.query(AuditLog).filter(AuditLog.action == AUDIT_ALERTS_CLEARED).count() == 1
    )


def test_soft_deleted_alert_is_not_detectable_as_duplicate(client, db):
    """软删除的 pending 告警不应再阻塞新告警（去重查询已排除软删除）。"""
    from app.services.detection import should_create_alert

    alert = Alert(
        username="dedup_soft",
        alert_type="frequency",
        alert_message="m",
        severity="medium",
        status="pending",
        deleted_at=_now(),
    )
    db.add(alert)
    db.commit()

    assert should_create_alert(db, "dedup_soft", "frequency") is True


def test_resolved_at_is_cleared_when_status_moves_away(client, db):
    headers = _make_admin(db)
    alert = Alert(
        username="revert_user",
        alert_type="device",
        alert_message="m",
        severity="medium",
        status="pending",
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)

    client.put(f"/api/alerts/{alert.id}", json={"status": "resolved"}, headers=headers)
    body = client.put(
        f"/api/alerts/{alert.id}", json={"status": "acknowledged"}, headers=headers
    ).json()

    assert body["status"] == "acknowledged"
    assert body["resolved_at"] is None, "回退状态后 resolved_at 必须清空"


def test_alert_status_change_is_audited(client, db):
    headers = _make_admin(db)
    alert = Alert(
        username="audit_user",
        alert_type="frequency",
        alert_message="m",
        severity="high",
        status="pending",
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)

    client.put(f"/api/alerts/{alert.id}", json={"status": "resolved"}, headers=headers)

    entry = db.query(AuditLog).filter(AuditLog.action == AUDIT_ALERT_STATUS_CHANGED).one()
    assert "pending → resolved" in entry.detail


def test_audit_logs_endpoint_lists_records(client, db):
    headers = _make_admin(db)
    client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})

    resp = client.get("/api/audit-logs", headers=headers)

    assert resp.status_code == 200
    assert resp.json()["total"] >= 1
    assert resp.json()["items"][0]["action"] == AUDIT_LOGIN_SUCCESS


# ─────────────── P1-6：登录审计与限流 ───────────────


def test_login_attempts_are_audited(client, db):
    _make_admin(db)

    client.post("/api/auth/login", json={"username": "admin", "password": "wrong"})
    client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})

    actions = {action for (action,) in db.query(AuditLog.action).all()}
    assert AUDIT_LOGIN_FAILED in actions
    assert AUDIT_LOGIN_SUCCESS in actions


def test_login_returns_429_when_limiter_blocks(client, db, monkeypatch):
    _make_admin(db)
    monkeypatch.setattr("app.core.ratelimit.is_blocked", lambda u, ip: (True, 30))

    resp = client.post(
        "/api/auth/login", json={"username": "admin", "password": "admin123"}
    )

    assert resp.status_code == 429
    assert resp.headers.get("retry-after") == "30"


def test_rate_limiter_fails_open_and_circuits(monkeypatch):
    """Redis 不可用时放行；且熔断后不再反复尝试连接（避免拖慢登录）。"""
    ratelimit.reset_circuit_breaker()
    calls = {"n": 0}

    def _boom():
        calls["n"] += 1
        raise OSError("redis unavailable")

    monkeypatch.setattr(ratelimit, "_client", _boom)

    assert ratelimit.is_blocked("someone", "127.0.0.1") == (False, 0)
    assert ratelimit.is_blocked("someone", "127.0.0.1") == (False, 0)
    assert calls["n"] == 1, "熔断期内的调用不应再次尝试连接 Redis"

    ratelimit.reset_circuit_breaker()


# ─────────────── P1-6：初始密码强制修改 ───────────────


def test_must_change_password_blocks_other_endpoints(client, db):
    _make_admin(db, username="fresh_admin", password="initpass123", must_change=True)

    login = client.post(
        "/api/auth/login", json={"username": "fresh_admin", "password": "initpass123"}
    )
    assert login.status_code == 200
    assert login.json()["must_change_password"] is True

    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    assert client.get("/api/alerts", headers=headers).status_code == 403


def test_change_password_flow_clears_flag(client, db):
    _make_admin(db, username="fresh_admin2", password="initpass123", must_change=True)

    token = client.post(
        "/api/auth/login", json={"username": "fresh_admin2", "password": "initpass123"}
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    wrong_old = client.post(
        "/api/auth/change-password",
        json={"old_password": "not-the-old-one", "new_password": "newpass123"},
        headers=headers,
    )
    assert wrong_old.status_code == 400

    too_short = client.post(
        "/api/auth/change-password",
        json={"old_password": "initpass123", "new_password": "short"},
        headers=headers,
    )
    assert too_short.status_code == 422

    changed = client.post(
        "/api/auth/change-password",
        json={"old_password": "initpass123", "new_password": "newpass123"},
        headers=headers,
    )
    assert changed.status_code == 200
    assert changed.json()["must_change_password"] is False

    new_headers = {"Authorization": f"Bearer {changed.json()['access_token']}"}
    assert client.get("/api/alerts", headers=new_headers).status_code == 200

    assert (
        client.post(
            "/api/auth/login", json={"username": "fresh_admin2", "password": "initpass123"}
        ).status_code
        == 401
    )

    entry = db.query(AuditLog).filter(AuditLog.action == AUDIT_PASSWORD_CHANGED).one()
    assert entry.target == "fresh_admin2"
