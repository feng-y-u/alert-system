import sqlite3
import hashlib

DB_PATH = "users.db"


def seed():
    conn = sqlite3.connect(DB_PATH)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'student'
        );
    """)

    users = [
        ("zhangsan", "123456", "student"),
        ("lisi", "123456", "student"),
        ("wangwu", "123456", "student"),
        ("zhaoliu", "123456", "student"),
        ("admin", "admin123", "admin"),
    ]

    for username, password, role in users:
        pw_hash = hashlib.sha256(password.encode()).hexdigest()
        try:
            conn.execute(
                "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                (username, pw_hash, role),
            )
        except sqlite3.IntegrityError:
            pass

    conn.commit()
    conn.close()
    print("Seeded 5 users.")


if __name__ == "__main__":
    seed()
