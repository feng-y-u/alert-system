"""快速测试异常检测（无需 Celery）"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import datetime, timedelta, timezone
from app.core.database import SessionLocal
from app.models.login_log import LoginLog
from app.models.alert import Alert
from app.schemas.login_log import LoginLogCreate
from app.services.logs import create_log
from app.services.detection import detect_frequency_anomaly, detect_device_anomaly, should_create_alert


def test_frequency_anomaly():
    print("=" * 50)
    print("测试1：频率异常检测")
    print("=" * 50)

    db = SessionLocal()
    try:
        # 先清空之前的测试数据
        db.query(Alert).delete()
        db.query(LoginLog).delete()
        db.commit()

        # 插入 15 条登录记录（5分钟内）
        now = datetime.now(timezone.utc)
        for i in range(15):
            log = LoginLog(
                username="testuser",
                login_time=now - timedelta(seconds=i * 20),
                ip_address="192.168.1.1",
                user_agent="Mozilla/5.0",
                login_status="success",
            )
            db.add(log)
        db.commit()
        print(f"[OK] 插入了 15 条登录记录")

        # 检测频率异常
        alert = detect_frequency_anomaly(db, "testuser")
        if alert:
            print(f"[告警] 严重级别: {alert.severity}")
            print(f"[告警] 消息: {alert.alert_message}")
        else:
            print("[无告警] 未检测到异常")

    finally:
        db.close()


def test_device_anomaly():
    print()
    print("=" * 50)
    print("测试2：设备异常检测")
    print("=" * 50)

    db = SessionLocal()
    try:
        # 清空之前的测试数据
        db.query(Alert).delete()
        db.query(LoginLog).delete()
        db.commit()

        # 插入 3 条不同设备/IP 的登录记录
        now = datetime.now(timezone.utc)
        devices = [
            ("192.168.1.1", "Mozilla/5.0 (Windows NT 10.0)"),
            ("192.168.1.2", "Mozilla/5.0 (iPhone; CPU iPhone OS)"),
            ("10.0.0.5", "Mozilla/5.0 (Linux; Android)"),
        ]
        for i, (ip, ua) in enumerate(devices):
            log = LoginLog(
                username="testuser",
                login_time=now - timedelta(minutes=i * 20),
                ip_address=ip,
                user_agent=ua,
                login_status="success",
            )
            db.add(log)
        db.commit()
        print(f"[OK] 插入了 3 条不同设备的登录记录")

        # 检测设备异常
        alert = detect_device_anomaly(db, "testuser")
        if alert:
            print(f"[告警] 严重级别: {alert.severity}")
            print(f"[告警] 消息: {alert.alert_message}")
        else:
            print("[无告警] 未检测到异常")

    finally:
        db.close()


def test_deduplication():
    print()
    print("=" * 50)
    print("测试3：告警去重")
    print("=" * 50)

    db = SessionLocal()
    try:
        username = "testuser"
        now = datetime.now(timezone.utc)

        # 先插入5条登录记录
        for i in range(5):
            log = LoginLog(
                username=username,
                login_time=now - timedelta(seconds=i * 30),
                ip_address="192.168.1.1",
                user_agent="Mozilla/5.0",
                login_status="success",
            )
            db.add(log)
        db.commit()

        # 先手动创建一个 pending 告警
        existing_alert = Alert(
            username=username,
            alert_type="frequency",
            alert_message="已有告警",
            severity="medium",
            status="pending",
        )
        db.add(existing_alert)
        db.commit()
        print(f"[OK] 已创建一条 pending 告警 (id={existing_alert.id})")

        # 检查去重：should_create_alert 应该返回 False
        can_create = should_create_alert(db, username, "frequency")
        print(f"[去重] 能否创建新告警: {can_create}（应为 False）")
        assert can_create is False, "去重逻辑失败！"

        # 修改告警状态为 resolved
        existing_alert.status = "resolved"
        db.commit()
        print(f"[OK] 修改告警状态为 resolved")

        # 现在应该可以创建新告警
        can_create = should_create_alert(db, username, "frequency")
        print(f"[去重] resolved 后能否创建新告警: {can_create}（应为 True）")
        assert can_create is True, "resolved 后应能创建新告警！"

        print("[去重] 告警去重逻辑全部通过")

    finally:
        db.close()


if __name__ == "__main__":
    test_frequency_anomaly()
    test_device_anomaly()
    test_deduplication()
    print()
    print("=" * 50)
    print("所有测试完成！")
    print("=" * 50)