"""统计口径一致性测试。

背景：仪表盘「待处理告警」与告警列表必须反映同一批数据，否则用户会看到
「仪表盘 0、列表一堆」这种自相矛盾的界面。本测试把两者的口径锁死：

    GET /api/stats 的 pendingAlerts
      == GET /api/alerts?status=pending 的 total
      == 库中 status='pending' 且未被软删除的告警数

覆盖要点：
- 三种状态混合时只计 pending；
- 软删除（deleted_at 非空）的告警不得计入；
- 已确认（acknowledged）不得被算作待处理。

见 docs/tech/14-评估与改进.md 的统计口径说明。
"""

from datetime import datetime, timezone

from app.core.security import create_access_token, get_password_hash
from app.models.alert import Alert
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


def _add_alert(db, username, status, deleted=False):
    alert = Alert(
        username=username,
        alert_type="frequency",
        alert_message=f"{status} alert",
        severity="medium",
        status=status,
        created_at=datetime.now(timezone.utc),
        deleted_at=datetime.now(timezone.utc) if deleted else None,
    )
    db.add(alert)
    db.commit()
    return alert


def test_pending_alerts_matches_alert_list(client, db):
    """仪表盘待处理数与告警列表 pending 筛选必须完全一致。"""
    headers = _admin_headers(db)

    _add_alert(db, "u_pending_1", "pending")
    _add_alert(db, "u_pending_2", "pending")
    _add_alert(db, "u_ack", "acknowledged")
    _add_alert(db, "u_resolved", "resolved")
    # 软删除的待处理告警：两个入口都必须排除
    _add_alert(db, "u_pending_deleted", "pending", deleted=True)

    stats = client.get("/api/stats", headers=headers).json()
    listed = client.get("/api/alerts?status=pending&limit=100", headers=headers).json()

    assert stats["pendingAlerts"] == 2, f"实际返回 {stats['pendingAlerts']}"
    assert listed["total"] == 2, f"实际返回 {listed['total']}"
    assert stats["pendingAlerts"] == listed["total"]


def test_pending_alerts_excludes_acknowledged(client, db):
    """已确认/已处理都不算「待处理」，避免把未闭环与已闭环混为一谈。"""
    headers = _admin_headers(db)

    _add_alert(db, "only_ack", "acknowledged")
    _add_alert(db, "only_resolved", "resolved")

    stats = client.get("/api/stats", headers=headers).json()
    assert stats["pendingAlerts"] == 0

    listed = client.get("/api/alerts?status=pending", headers=headers).json()
    assert listed["total"] == 0


def test_pending_alerts_counts_all_pending_regardless_of_age(client, db):
    """待处理数不做时间窗口过滤：只按状态统计。

    （趋势图才按业务时区逐日统计；两者口径不同是刻意的，
      这里锁定旧行为，防止有人给待处理数加上"近 7 天"之类的窗口。）
    """
    headers = _admin_headers(db)

    old = _add_alert(db, "u_old_pending", "pending")
    old.created_at = datetime(2020, 1, 1, tzinfo=timezone.utc)
    db.commit()
    _add_alert(db, "u_new_pending", "pending")

    stats = client.get("/api/stats", headers=headers).json()
    listed = client.get("/api/alerts?status=pending", headers=headers).json()

    assert stats["pendingAlerts"] == 2
    assert listed["total"] == 2


def test_pending_alerts_matches_list_after_status_change(client, db):
    """把待处理告警改成已处理后，两个入口必须同步下降。"""
    headers = _admin_headers(db)
    alert = _add_alert(db, "u_transition", "pending")

    assert client.get("/api/stats", headers=headers).json()["pendingAlerts"] == 1

    client.put(f"/api/alerts/{alert.id}", json={"status": "acknowledged"}, headers=headers)

    stats = client.get("/api/stats", headers=headers).json()
    listed = client.get("/api/alerts?status=pending", headers=headers).json()
    assert stats["pendingAlerts"] == 0
    assert listed["total"] == 0
    # 告警本身仍在列表中（只是状态变了）
    assert client.get("/api/alerts", headers=headers).json()["total"] == 1
