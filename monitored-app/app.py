import sqlite3
import random
import hashlib
import time
import requests
from datetime import datetime, timezone
from flask import Flask, render_template, request, redirect, jsonify

app = Flask(__name__)
app.secret_key = "monitored-app-dev-key"

DB_PATH = "users.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'student'
            );
        """)


@app.route("/", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        pw_hash = hashlib.sha256(password.encode()).hexdigest()

        with get_db() as db:
            user = db.execute(
                "SELECT * FROM users WHERE username = ? AND password = ?",
                (username, pw_hash),
            ).fetchone()

        if user:
            report_log({
                "username": username,
                "login_time": datetime.now(timezone.utc).isoformat(),
                "ip_address": request.remote_addr or "127.0.0.1",
                "user_agent": request.headers.get("User-Agent", "Unknown"),
                "login_status": "success",
            }, request.form.get("platform_url", "http://localhost:8000"),
               request.form.get("api_key", "change-me-to-a-random-api-key-in-production"))
            return redirect(f"/welcome?username={username}")
        else:
            error = "用户名或密码错误"
            report_log({
                "username": username,
                "login_time": datetime.now(timezone.utc).isoformat(),
                "ip_address": request.remote_addr or "127.0.0.1",
                "user_agent": request.headers.get("User-Agent", "Unknown"),
                "login_status": "failed",
            }, request.form.get("platform_url", "http://localhost:8000"),
               request.form.get("api_key", "change-me-to-a-random-api-key-in-production"))

    return render_template("index.html", error=error)


@app.route("/welcome")
def welcome():
    username = request.args.get("username", "用户")
    return render_template("welcome.html", username=username)


def report_log(data: dict, platform_url: str, api_key: str) -> bool:
    try:
        resp = requests.post(
            f"{platform_url.rstrip('/')}/api/logs",
            json=data,
            headers={"X-API-Key": api_key},
            timeout=5,
        )
        return resp.status_code == 201
    except requests.RequestException:
        return False


@app.route("/api/simulate", methods=["POST"])
def simulate():
    body = request.get_json()
    sim_type = body.get("type")
    platform_url = body.get("platform_url", "http://localhost:8000")
    api_key = body.get("api_key", "change-me-to-a-random-api-key-in-production")
    logs = []

    if sim_type == "frequency":
        ip = f"192.168.1.{random.randint(100, 200)}"
        for i in range(10):
            data = {
                "username": "zhaoliu",
                "login_time": datetime.now(timezone.utc).isoformat(),
                "ip_address": ip,
                "user_agent": "Mozilla/5.0 (Windows NT 10.0)",
                "login_status": "failed",
            }
            ok = report_log(data, platform_url, api_key)
            status = "✓" if ok else "✗"
            logs.append({"msg": f"[{status}] 频率 {i+1}/10  zhaoliu  {ip}", "dim": True})
            if i < 9:
                time.sleep(random.uniform(8, 12))
    elif sim_type == "device":
        devices = [
            ("192.168.1.10", "Mozilla/5.0 (Windows NT 10.0)"),
            ("10.0.0.20", "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0)"),
            ("172.16.0.30", "Mozilla/5.0 (Linux; Android 14)"),
        ]
        for ip, ua in devices:
            data = {
                "username": "wangwu",
                "login_time": datetime.now(timezone.utc).isoformat(),
                "ip_address": ip,
                "user_agent": ua,
                "login_status": "failed",
            }
            ok = report_log(data, platform_url, api_key)
            status = "✓" if ok else "✗"
            logs.append({"msg": f"[{status}] 设备  {ip}  {ua[:30]}...", "dim": True})
    else:
        return jsonify({"logs": [{"msg": f"未知类型: {sim_type}"}]})

    logs.append({"msg": "模拟完成 ✓", "dim": False})
    return jsonify({"logs": logs})


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
