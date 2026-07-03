"""Seed 脚本：初始化默认管理员账号

用法：
    python scripts/seed.py
"""

import sys
import os

# 确保能导入 app 模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.user import User


def create_default_admin():
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == "admin").first()
        if existing:
            print("[OK] 管理员 admin 已存在，跳过创建")
            return

        admin = User(
            username="admin",
            email="admin@campus.edu",
            hashed_password=get_password_hash("admin123"),
            role="admin",
            is_active=True,
        )
        db.add(admin)
        db.commit()
        print("[OK] 默认管理员创建成功")
        print(f"   用户名: admin")
        print(f"   邮箱:   admin@campus.edu")
        print(f"   密码:   admin123")
    except Exception as e:
        db.rollback()
        print(f"[ERR] 创建失败: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    create_default_admin()