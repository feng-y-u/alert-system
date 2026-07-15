"""告警统计接口测试"""

from app.core.security import create_access_token, get_password_hash
from app.models.user import User


def _seed_and_auth(db):
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
    token = create_access_token(data={"sub": str(user.id)})
    return {"Authorization": f"Bearer {token}"}


def test_alert_stats_requires_auth(client):
    """未登录访问 /api/stats/alerts 返回 401"""
    resp = client.get("/api/stats/alerts")
    assert resp.status_code == 401


def test_alert_stats_structure(client, db):
    """登录后返回包含三个聚合 key 的结构"""
    resp = client.get("/api/stats/alerts", headers=_seed_and_auth(db))
    assert resp.status_code == 200
    data = resp.json()
    assert "alertTrend" in data
    assert "typeDist" in data
    assert "severityDist" in data


def test_alert_stats_trend_length_default(client, db):
    """默认 days=7，alertTrend 长度为 7"""
    resp = client.get("/api/stats/alerts", headers=_seed_and_auth(db))
    data = resp.json()
    assert len(data["alertTrend"]) == 7


def test_alert_stats_trend_length_30(client, db):
    """days=30 时 alertTrend 长度为 30"""
    resp = client.get("/api/stats/alerts?days=30", headers=_seed_and_auth(db))
    data = resp.json()
    assert len(data["alertTrend"]) == 30
