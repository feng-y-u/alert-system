"""异常检测服务测试"""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.orm import Session

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


def test_detect_device_anomaly_multiple_devices(db: Session):
    """测试多设备登录（触发告警）"""
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
    assert alert.severity == "high"
    assert "3 个不同设备" in alert.alert_message


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