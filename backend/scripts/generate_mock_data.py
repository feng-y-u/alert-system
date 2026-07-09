"""生成模拟登录日志和告警数据

用法：
    cd backend
    $env:PYTHONPATH="."; python scripts/generate_mock_data.py
"""

import sys
import os
import random
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.database import SessionLocal
from app.models.login_log import LoginLog
from app.models.alert import Alert

# 模拟数据配置
USERS = ["zhangsan", "lisi", "wangwu", "zhaoliu", "sunqi", "zhouba"]
IPS = [
    "10.0.0.1", "10.0.0.2", "10.0.0.3", "10.0.0.4",
    "192.168.1.100", "192.168.1.101", "172.16.0.50",
]
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Edge/120.0.0.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0) Mobile/15E148",
    "Mozilla/5.0 (Linux; Android 14) Chrome/120.0.0.0 Mobile",
]
LOCATIONS = ["教学楼A", "图书馆", "宿舍区", "实验楼", "行政楼", "校外", ""]


def generate_mock_data():
    db = SessionLocal()
    try:
        # 先清空旧数据
        db.query(Alert).delete()
        db.query(LoginLog).delete()
        db.commit()

        now = datetime.now(timezone.utc)
        logins = []
        alerts = []

        # 生成 7 天的登录日志
        for day_offset in range(7, -1, -1):
            date = now - timedelta(days=day_offset)
            # 每天每个用户 3-15 次登录
            for user in USERS:
                login_count = random.randint(3, 15)
                for _ in range(login_count):
                    hour = random.randint(6, 23)
                    minute = random.randint(0, 59)
                    login_time = date.replace(hour=hour, minute=minute, second=random.randint(0, 59))

                    # 85% 成功，15% 失败
                    is_success = random.random() < 0.85
                    logins.append(LoginLog(
                        username=user,
                        login_time=login_time,
                        ip_address=random.choice(IPS),
                        user_agent=random.choice(USER_AGENTS),
                        login_status="success" if is_success else "failure",
                        location=random.choice(LOCATIONS),
                    ))

                    # 失败登录超过阈值时生成频率异常告警
                    if not is_success and random.random() < 0.3:
                        alerts.append(Alert(
                            username=user,
                            alert_type="frequency",
                            alert_message=f"用户 {user} 短时间内多次登录失败",
                            severity="medium",
                            status="pending",
                            created_at=login_time,
                            updated_at=login_time,
                        ))

        db.bulk_save_objects(logins)
        db.bulk_save_objects(alerts)
        db.commit()

        print(f"[OK] 生成 {len(logins)} 条登录日志, {len(alerts)} 条告警")
        print(f"     用户名: admin / admin123")
    except Exception as e:
        db.rollback()
        print(f"[ERR] 生成失败: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    generate_mock_data()