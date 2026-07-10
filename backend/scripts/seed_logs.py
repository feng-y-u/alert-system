"""种子脚本：插入测试登录日志数据

用法：
    cd backend
    $env:PYTHONPATH = "E:\实习\backend"; python scripts/seed_logs.py
"""

import sys
import os
import random
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.database import SessionLocal
from app.models.login_log import LoginLog

# 测试用户
USERS = ["张三", "李四", "王五", "赵六", "钱七", "孙八", "周九", "吴十",
         "test01", "test02", "teacher_li", "teacher_wang", "admin_zhang"]

# 测试 IP
IP_ADDRESSES = [
    "192.168.1.100", "192.168.1.101", "10.0.0.5", "10.0.0.10",
    "172.16.0.1", "172.16.0.50", "202.114.1.1", "202.114.2.88",
    "114.114.114.114", "8.8.8.8", "203.0.113.42", "198.51.100.7",
]

# 测试 User-Agent
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 Chrome/120.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/119.0.0.0 Safari/537.36",
    "PostmanRuntime/7.36.0",
    "Python-urllib/3.11",
    None,
]

# 状态（80% 成功，20% 失败）
STATUSES = ["success"] * 8 + ["failure"] * 2


def seed_login_logs(count: int = 200):
    db = SessionLocal()
    try:
        # 先清空已有数据（可选）
        existing = db.query(LoginLog).count()
        if existing > 0:
            print(f"[INFO] 已存在 {existing} 条日志，跳过插入（如需重置先手动清空表）")
            return

        now = datetime.now(timezone.utc)
        logs = []

        for i in range(count):
            # 随机分布在过去 14 天内
            days_ago = random.randint(0, 14)
            hours_ago = random.randint(0, 23)
            minutes_ago = random.randint(0, 59)

            login_time = now - timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago)

            log = LoginLog(
                username=random.choice(USERS),
                login_time=login_time,
                ip_address=random.choice(IP_ADDRESSES),
                user_agent=random.choice(USER_AGENTS),
                login_status=random.choice(STATUSES),
                location=None,  # 地理位置字段已弃用
            )
            logs.append(log)

        db.add_all(logs)
        db.commit()
        print(f"[OK] 成功插入 {count} 条测试登录日志")

        # 统计信息
        success_count = db.query(LoginLog).filter(LoginLog.login_status == "success").count()
        failure_count = db.query(LoginLog).filter(LoginLog.login_status == "failure").count()
        print(f"    成功: {success_count} 条")
        print(f"    失败: {failure_count} 条")
        print(f"    用户数: {db.query(LoginLog.username).distinct().count()}")
        print(f"    时间范围: 过去 14 天")

    except Exception as e:
        db.rollback()
        print(f"[ERR] 插入失败: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_login_logs(200)