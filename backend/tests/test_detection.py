"""异常检测服务测试"""

import threading
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.core.database import Base
from app.models.alert import Alert
from app.models.login_log import LoginLog
from app.schemas.login_log import LoginLogCreate
from app.services.detection import (
    detect_device_anomaly,
    detect_frequency_anomaly,
    should_create_alert,
)
from app.services.logs import create_log


def test_detect_frequency_anomaly_normal(db: Session):
    """测试正常登录频率（不触发告警）"""
    # 创建5条登录记录（间隔1分钟）
    for i in range(5):
        log_data = LoginLogCreate(
            username="testuser",
            login_time=datetime.now(timezone.utc) - timedelta(minutes=i),
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            login_status="success"
        )
        create_log(db, log_data)

    # 检测
    alert = detect_frequency_anomaly(db, "testuser")
    assert alert is None


def test_detect_frequency_anomaly_medium(db: Session):
    """测试中等级别频率异常（10-30次）"""
    # 创建15条登录记录（5分钟内）
    base_time = datetime.now(timezone.utc)
    for i in range(15):
        log_data = LoginLogCreate(
            username="testuser",
            login_time=base_time - timedelta(seconds=i*20),
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            login_status="success"
        )
        create_log(db, log_data)

    # 检测
    alert = detect_frequency_anomaly(db, "testuser")
    assert alert is not None
    assert alert.severity == "medium"
    assert alert.alert_type == "frequency"


def test_detect_frequency_anomaly_high(db: Session):
    """测试高级别频率异常（>30次）"""
    # 创建35条登录记录（5分钟内）
    base_time = datetime.now(timezone.utc)
    for i in range(35):
        log_data = LoginLogCreate(
            username="testuser",
            login_time=base_time - timedelta(seconds=i*8),
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            login_status="success"
        )
        create_log(db, log_data)

    # 检测
    alert = detect_frequency_anomaly(db, "testuser")
    assert alert is not None
    assert alert.severity == "high"


def test_detect_device_anomaly_single_device(db: Session):
    """测试单设备登录（不触发告警）"""
    base_time = datetime.now(timezone.utc)
    for i in range(3):
        log_data = LoginLogCreate(
            username="testuser",
            login_time=base_time - timedelta(minutes=i*10),
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0 (Windows NT 10.0)",
            login_status="success"
        )
        create_log(db, log_data)

    alert = detect_device_anomaly(db, "testuser")
    assert alert is None


def test_detect_device_anomaly_two_devices_no_alert(db: Session):
    """测试 2 个设备登录（低于检测起点，不触发告警）"""
    base_time = datetime.now(timezone.utc)

    # 设备1
    log_data = LoginLogCreate(
        username="testuser",
        login_time=base_time - timedelta(minutes=20),
        ip_address="192.168.1.1",
        user_agent="Mozilla/5.0 (Windows NT 10.0)",
        login_status="success"
    )
    create_log(db, log_data)

    # 设备2
    log_data = LoginLogCreate(
        username="testuser",
        login_time=base_time - timedelta(minutes=10),
        ip_address="192.168.1.2",
        user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS)",
        login_status="success"
    )
    create_log(db, log_data)

    alert = detect_device_anomaly(db, "testuser")
    assert alert is None


def test_detect_device_anomaly_multiple_devices(db: Session):
    """测试 3 个设备登录（触发中级告警）"""
    base_time = datetime.now(timezone.utc)

    # 设备1
    log_data = LoginLogCreate(
        username="testuser",
        login_time=base_time - timedelta(minutes=30),
        ip_address="192.168.1.1",
        user_agent="Mozilla/5.0 (Windows NT 10.0)",
        login_status="success"
    )
    create_log(db, log_data)

    # 设备2
    log_data = LoginLogCreate(
        username="testuser",
        login_time=base_time - timedelta(minutes=20),
        ip_address="192.168.1.2",
        user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS)",
        login_status="success"
    )
    create_log(db, log_data)

    # 设备3
    log_data = LoginLogCreate(
        username="testuser",
        login_time=base_time - timedelta(minutes=10),
        ip_address="192.168.1.3",
        user_agent="Mozilla/5.0 (Linux; Android)",
        login_status="success"
    )
    create_log(db, log_data)

    alert = detect_device_anomaly(db, "testuser")
    assert alert is not None
    assert alert.severity == "medium"
    assert "3 个不同设备" in alert.alert_message


def test_detect_device_anomaly_high_severity(db: Session):
    """测试 5 个设备登录（触发高级告警）"""
    base_time = datetime.now(timezone.utc)

    for i in range(5):
        log_data = LoginLogCreate(
            username="testuser",
            login_time=base_time - timedelta(minutes=(5 - i) * 5),
            ip_address=f"192.168.1.{i + 1}",
            user_agent=f"Mozilla/5.0 (Device {i + 1})",
            login_status="success"
        )
        create_log(db, log_data)

    alert = detect_device_anomaly(db, "testuser")
    assert alert is not None
    assert alert.severity == "high"
    assert "5 个不同设备" in alert.alert_message


def test_should_create_alert_deduplication(db: Session):
    """测试告警去重逻辑"""
    # 创建第一个告警
    alert1 = Alert(
        username="testuser",
        alert_type="frequency",
        alert_message="Test",
        severity="medium",
        status="pending"
    )
    db.add(alert1)
    db.commit()

    # 24小时内应该不创建新告警
    should_create = should_create_alert(db, "testuser", "frequency")
    assert should_create is False

    # 修改状态为 resolved
    alert1.status = "resolved"
    db.commit()

    # 现在可以创建新告警
    should_create = should_create_alert(db, "testuser", "frequency")
    assert should_create is True


# ─────────────── 并发去重（BUG-002）───────────────
# 去重原本是「先 SELECT 再 INSERT」的 check-then-act，两条并发日志各自投递一次
# 检测任务时，两个任务都可能查到「没有 pending 告警」于是各插一条。
# 修复后由唯一索引 uq_alerts_pending_dedup 在数据库层保证不变量。


def _seed_high_frequency_logs(db: Session, username: str, count: int = 12):
    """写入 ``count`` 条 5 分钟内的日志，返回按 id 升序的 (id, login_time)。"""
    base = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=1)
    for i in range(count):
        db.add(
            LoginLog(
                username=username,
                login_time=base + timedelta(seconds=i),
                ip_address="10.0.0.1",
                user_agent="pytest",
                login_status="failure",
            )
        )
    db.commit()
    rows = (
        db.query(LoginLog.id, LoginLog.login_time)
        .filter(LoginLog.username == username)
        .order_by(LoginLog.id)
        .all()
    )
    return rows


def test_duplicate_pending_alert_is_rejected_by_unique_index(db: Session):
    """同一 (username, alert_type) 的第二条 pending 告警必须被数据库拒绝。"""
    db.add(Alert(username="dup", alert_type="frequency", alert_message="a",
                 severity="medium", status="pending"))
    db.commit()

    db.add(Alert(username="dup", alert_type="frequency", alert_message="b",
                 severity="high", status="pending"))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()

    assert db.query(Alert).filter_by(username="dup", alert_type="frequency").count() == 1


def test_different_alert_type_is_allowed(db: Session):
    """不同类型可以各有一条 pending。"""
    db.add(Alert(username="dup2", alert_type="frequency", alert_message="a",
                 severity="medium", status="pending"))
    db.add(Alert(username="dup2", alert_type="device", alert_message="b",
                 severity="medium", status="pending"))
    db.commit()
    assert db.query(Alert).filter_by(username="dup2").count() == 2


def test_resolved_frees_the_pending_slot(db: Session):
    """状态离开 pending 后，同类型可以再建 pending（与既有去重语义一致）。"""
    first = Alert(username="dup3", alert_type="frequency", alert_message="a",
                  severity="medium", status="pending")
    db.add(first)
    db.commit()

    first.status = "resolved"
    db.commit()

    db.add(Alert(username="dup3", alert_type="frequency", alert_message="b",
                 severity="high", status="pending"))
    db.commit()
    assert db.query(Alert).filter_by(username="dup3", alert_type="frequency").count() == 2


def test_soft_deleted_alert_frees_the_pending_slot(db: Session):
    """软删除后不再占用去重槽位。"""
    first = Alert(username="dup4", alert_type="frequency", alert_message="a",
                  severity="medium", status="pending")
    db.add(first)
    db.commit()

    first.deleted_at = datetime.now(timezone.utc)
    db.commit()

    db.add(Alert(username="dup4", alert_type="frequency", alert_message="b",
                 severity="high", status="pending"))
    db.commit()
    assert db.query(Alert).filter_by(username="dup4").count() == 2


def test_concurrent_detection_creates_single_alert(engine):
    """两个线程并发检测同一用户时，只应产生一条告警（BUG-002 回归）。

    修复前实测稳定复现 2 条重复告警。
    """
    TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    setup = TestingSessionLocal()
    rows = _seed_high_frequency_logs(setup, "race")
    target_ids = [rows[-2][0], rows[-1][0]]  # 末两条：回看窗口内都有 10+ 条
    setup.close()

    barrier = threading.Barrier(2)
    errors = []
    lock = threading.Lock()

    def worker(log_id):
        session = TestingSessionLocal()
        try:
            barrier.wait(timeout=5)  # 尽量让两个线程同时进入检测
            detect_frequency_anomaly(session, "race", log_id)
        except Exception as exc:  # noqa: BLE001 - 收集后统一断言
            with lock:
                errors.append(exc)
        finally:
            session.close()

    threads = [threading.Thread(target=worker, args=(lid,)) for lid in target_ids]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=30)
    assert not errors, f"并发检测抛出异常：{errors}"

    check = TestingSessionLocal()
    try:
        alerts = check.query(Alert).filter_by(username="race", alert_type="frequency").all()
        assert len(alerts) == 1, (
            f"并发去重失效：产生 {len(alerts)} 条 pending 告警（期望 1）"
        )
        assert alerts[0].status == "pending"
    finally:
        check.close()