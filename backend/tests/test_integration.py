"""端到端集成测试：认证 → 日志写入 → 异常检测 → 告警生成 → 告警 API → 统计"""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from app.core.security import create_access_token, get_password_hash
from app.models.user import User
from app.models.alert import Alert
from app.models.login_log import LoginLog
from app.schemas.login_log import LoginLogCreate
from app.services.detection import (
    detect_device_anomaly,
    detect_frequency_anomaly,
    should_create_alert,
)
from app.services.logs import create_log


def _seed_admin(db) -> User:
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
    return user


def _auth_headers(user: User) -> dict:
    token = create_access_token(data={"sub": str(user.id)})
    return {"Authorization": f"Bearer {token}"}


# ─── 认证集成测试 ───────────────────────────────────────────────


class TestAuthIntegration:
    def test_login_success(self, client, db):
        _seed_admin(db)
        resp = client.post("/api/auth/login", json={
            "username": "admin",
            "password": "admin123",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data

    def test_login_failed_wrong_password(self, client, db):
        _seed_admin(db)
        resp = client.post("/api/auth/login", json={
            "username": "admin",
            "password": "wrong",
        })
        assert resp.status_code == 401

    def test_login_failed_nonexistent_user(self, client, db):
        resp = client.post("/api/auth/login", json={
            "username": "nobody",
            "password": "nobody",
        })
        assert resp.status_code == 401

    def test_get_me_with_valid_token(self, client, db):
        user = _seed_admin(db)
        resp = client.get("/api/auth/me", headers=_auth_headers(user))
        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == "admin"

    def test_get_me_without_token_returns_401(self, client, db):
        resp = client.get("/api/auth/me")
        assert resp.status_code == 401

    def test_register_requires_auth(self, client, db):
        user = _seed_admin(db)
        resp = client.post("/api/auth/register", json={
            "username": "newadmin",
            "email": "new@test.com",
            "password": "newadmin123",
        }, headers=_auth_headers(user))
        assert resp.status_code == 200
        assert resp.json()["username"] == "newadmin"

    def test_register_duplicate_username(self, client, db):
        user = _seed_admin(db)
        resp = client.post("/api/auth/register", json={
            "username": "admin",
            "email": "another@test.com",
            "password": "admin123",
        }, headers=_auth_headers(user))
        assert resp.status_code == 400


# ─── 日志集成测试 ───────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _mock_celery_delay():
    with patch("app.tasks.detection.detect_anomaly_for_log.delay", return_value=None):
        yield


class TestLogsIntegration:
    def test_post_log_with_api_key(self, client, db):
        resp = client.post("/api/logs", json={
            "username": "student01",
            "login_time": datetime.now(timezone.utc).isoformat(),
            "ip_address": "10.0.0.1",
            "user_agent": "Mozilla/5.0",
            "login_status": "success",
            "location": "北京",
        }, headers={"X-API-Key": "dev-api-key-change-in-production"})
        assert resp.status_code == 201
        data = resp.json()
        assert data["username"] == "student01"
        assert data["id"] is not None

    def test_post_log_wrong_api_key(self, client, db):
        resp = client.post("/api/logs", json={
            "username": "student01",
            "login_time": datetime.now(timezone.utc).isoformat(),
            "ip_address": "10.0.0.2",
            "user_agent": "Mozilla/5.0",
            "login_status": "success",
        }, headers={"X-API-Key": "wrong-key"})
        assert resp.status_code == 401

    def test_post_log_missing_api_key(self, client, db):
        resp = client.post("/api/logs", json={
            "username": "student01",
            "login_time": datetime.now(timezone.utc).isoformat(),
            "ip_address": "10.0.0.3",
            "user_agent": "Mozilla/5.0",
            "login_status": "success",
        })
        assert resp.status_code == 422

    def test_get_logs_requires_auth(self, client, db):
        resp = client.get("/api/logs")
        assert resp.status_code == 401

    def test_get_logs_with_auth(self, client, db):
        user = _seed_admin(db)
        resp = client.get("/api/logs", headers=_auth_headers(user))
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data


# ─── 异常检测集成测试 ──────────────────────────────────────────


class TestDetectionIntegration:
    def test_frequency_detection_triggers_alert(self, client, db):
        base_time = datetime.now(timezone.utc)
        api_headers = {"X-API-Key": "dev-api-key-change-in-production"}

        for i in range(15):
            client.post("/api/logs", json={
                "username": "spammer",
                "login_time": (base_time - timedelta(seconds=i * 20)).isoformat(),
                "ip_address": "192.168.1.100",
                "user_agent": "Mozilla/5.0",
                "login_status": "success",
            }, headers=api_headers)

        alert = detect_frequency_anomaly(db, "spammer")
        assert alert is not None
        assert alert.alert_type == "frequency"
        assert alert.severity in ("medium", "high")
        assert alert.username == "spammer"

    def test_device_detection_triggers_alert(self, client, db):
        base_time = datetime.now(timezone.utc)
        api_headers = {"X-API-Key": "dev-api-key-change-in-production"}
        devices = [
            ("192.168.1.1", "Mozilla/5.0 (Windows)"),
            ("10.0.0.1", "Mozilla/5.0 (iPhone)"),
            ("172.16.0.1", "Mozilla/5.0 (Android)"),
        ]

        for n, (ip, ua) in enumerate(devices):
            client.post("/api/logs", json={
                "username": "traveler",
                "login_time": (base_time - timedelta(minutes=n * 10)).isoformat(),
                "ip_address": ip,
                "user_agent": ua,
                "login_status": "success",
            }, headers=api_headers)

        alert = detect_device_anomaly(db, "traveler")
        assert alert is not None
        assert alert.alert_type == "device"
        assert alert.severity == "high"
        assert "3 个不同设备" in alert.alert_message

    def test_normal_behavior_no_alert(self, client, db):
        base_time = datetime.now(timezone.utc)
        api_headers = {"X-API-Key": "dev-api-key-change-in-production"}

        for i in range(3):
            client.post("/api/logs", json={
                "username": "normaluser",
                "login_time": (base_time - timedelta(minutes=i * 10)).isoformat(),
                "ip_address": "192.168.1.50",
                "user_agent": "Mozilla/5.0",
                "login_status": "success",
            }, headers=api_headers)

        alert = detect_frequency_anomaly(db, "normaluser")
        assert alert is None

        alert = detect_device_anomaly(db, "normaluser")
        assert alert is None


# ─── 告警 API 集成测试 ──────────────────────────────────────────


class TestAlertsIntegration:
    def test_list_alerts_requires_auth(self, client, db):
        resp = client.get("/api/alerts")
        assert resp.status_code == 401

    def test_list_alerts_returns_structure(self, client, db):
        user = _seed_admin(db)
        resp = client.get("/api/alerts", headers=_auth_headers(user))
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data

    def test_list_alerts_with_status_filter(self, client, db):
        user = _seed_admin(db)
        alert = Alert(
            username="testuser",
            alert_type="frequency",
            alert_message="Test alert",
            severity="high",
            status="pending",
        )
        db.add(alert)
        db.commit()

        resp = client.get("/api/alerts?status=pending", headers=_auth_headers(user))
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1

    def test_update_alert_status(self, client, db):
        user = _seed_admin(db)
        alert = Alert(
            username="testuser",
            alert_type="device",
            alert_message="Update me",
            severity="medium",
            status="pending",
        )
        db.add(alert)
        db.commit()

        resp = client.put(f"/api/alerts/{alert.id}", json={"status": "resolved"}, headers=_auth_headers(user))
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "resolved"
        assert data["resolved_at"] is not None

    def test_get_single_alert(self, client, db):
        user = _seed_admin(db)
        alert = Alert(
            username="testuser",
            alert_type="frequency",
            alert_message="Get me",
            severity="low",
            status="pending",
        )
        db.add(alert)
        db.commit()

        resp = client.get(f"/api/alerts/{alert.id}", headers=_auth_headers(user))
        assert resp.status_code == 200
        assert resp.json()["alert_message"] == "Get me"

    def test_get_nonexistent_alert(self, client, db):
        user = _seed_admin(db)
        resp = client.get("/api/alerts/99999", headers=_auth_headers(user))
        assert resp.status_code == 404


# ─── 统计 API 集成测试 ─────────────────────────────────────────


class TestStatsIntegration:
    def test_stats_empty_data(self, client, db):
        user = _seed_admin(db)
        resp = client.get("/api/stats/alerts", headers=_auth_headers(user))
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["alertTrend"]) == 7
        assert isinstance(data["typeDist"], list)
        assert isinstance(data["severityDist"], list)

    def test_stats_with_alert_data(self, client, db):
        user = _seed_admin(db)
        now = datetime.now(timezone.utc)
        for i in range(5):
            alert = Alert(
                username="statuser",
                alert_type="frequency",
                alert_message=f"Alert {i}",
                severity="medium" if i % 2 == 0 else "high",
                status="pending",
                created_at=now - timedelta(days=i),
            )
            db.add(alert)
        db.commit()

        resp = client.get("/api/stats/alerts", headers=_auth_headers(user))
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["alertTrend"]) == 7
        total = sum(d["count"] for d in data["alertTrend"])
        assert total == 5


# ─── 去重逻辑测试 ──────────────────────────────────────────────


class TestDeduplication:
    def test_should_create_alert_returns_false_with_existing_pending(self, db):
        alert = Alert(
            username="dup_user",
            alert_type="frequency",
            alert_message="Existing",
            severity="medium",
            status="pending",
        )
        db.add(alert)
        db.commit()

        assert should_create_alert(db, "dup_user", "frequency") is False

    def test_should_create_alert_returns_true_after_resolved(self, db):
        alert = Alert(
            username="dup_user2",
            alert_type="frequency",
            alert_message="Resolved alert",
            severity="medium",
            status="resolved",
        )
        db.add(alert)
        db.commit()

        assert should_create_alert(db, "dup_user2", "frequency") is True

    def test_should_create_alert_different_type_is_allowed(self, db):
        alert = Alert(
            username="dup_user3",
            alert_type="frequency",
            alert_message="Freq alert",
            severity="medium",
            status="pending",
        )
        db.add(alert)
        db.commit()

        assert should_create_alert(db, "dup_user3", "device") is True


# ─── SSE Pub 测试 ──────────────────────────────────────────────


class TestSSEPublish:
    def test_publish_alert_event(self, db):
        alert = Alert(
            username="sseuser",
            alert_type="frequency",
            alert_message="SSE test",
            severity="high",
            status="pending",
        )
        db.add(alert)
        db.commit()

        with patch("app.tasks.detection.redis.from_url") as mock_redis:
            mock_client = MagicMock()
            mock_redis.return_value = mock_client

            from app.tasks.detection import _publish_alert_event
            _publish_alert_event(alert)

            mock_client.publish.assert_called_once()
            call_args = mock_client.publish.call_args[0]
            assert call_args[0] == "alerts"

    def test_publish_alert_event_handles_redis_error(self, db):
        alert = Alert(
            username="sseuser2",
            alert_type="device",
            alert_message="SSE error test",
            severity="low",
            status="pending",
        )
        db.add(alert)
        db.commit()

        with patch("app.tasks.detection.redis.from_url") as mock_redis:
            mock_redis.side_effect = Exception("Redis down")

            from app.tasks.detection import _publish_alert_event
            _publish_alert_event(alert)


# ─── 端到端全流程测试 ─────────────────────────────────────────


class TestEndToEnd:
    def test_full_pipeline_auth_to_alert(self, client, db):
        """模拟完整流程：登录 → 写入日志 → 触发检测 → 验证告警 → 查询告警 API"""
        user = _seed_admin(db)
        token_headers = _auth_headers(user)
        api_headers = {"X-API-Key": "dev-api-key-change-in-production"}

        assert client.get("/api/auth/me", headers=token_headers).status_code == 200

        base_time = datetime.now(timezone.utc)
        for i in range(20):
            resp = client.post("/api/logs", json={
                "username": "target_user",
                "login_time": (base_time - timedelta(seconds=i * 15)).isoformat(),
                "ip_address": "10.10.10.10",
                "user_agent": "Mozilla/5.0",
                "login_status": "success",
                "location": "上海",
            }, headers=api_headers)
            assert resp.status_code == 201

        resp = client.get("/api/logs?username=target_user", headers=token_headers)
        assert resp.status_code == 200
        assert resp.json()["total"] >= 20

        alert = detect_frequency_anomaly(db, "target_user")
        assert alert is not None
        assert alert.alert_type == "frequency"
        assert alert.username == "target_user"

        resp = client.get("/api/alerts?username=target_user", headers=token_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        alert_from_api = data["items"][0]
        assert alert_from_api["username"] == "target_user"
        assert alert_from_api["alert_type"] == "frequency"

        alert_id = alert_from_api["id"]
        resp = client.put(f"/api/alerts/{alert_id}", json={"status": "resolved"}, headers=token_headers)
        assert resp.status_code == 200
        assert resp.json()["status"] == "resolved"

        resp = client.get("/api/stats/alerts", headers=token_headers)
        assert resp.status_code == 200
