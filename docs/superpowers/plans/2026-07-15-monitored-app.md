# 被监控方模拟器实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个轻量 Flask 模拟器，模拟校园系统登录行为，向监控平台上报日志，并支持一键触发频率/设备异常。

**架构:** Flask + SQLite（本地用户库）+ requests（上报到监控平台 `/api/logs`）。前端通过 POST 将平台配置传给 Flask 后端，后端用配置中的 `platform_url` 和 `api_key` 上报日志。

**Tech Stack:** Python Flask, SQLite, requests

---

### Task 1: 项目脚手架

**Files:**
- Create: `monitored-app/app.py`
- Create: `monitored-app/requirements.txt`
- Create: `monitored-app/seed.py`
- Create: `monitored-app/templates/index.html`
- Create: `monitored-app/templates/welcome.html`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p monitored-app/templates
```

- [ ] **Step 2: Write requirements.txt**

```txt
flask==3.0.0
requests==2.31.0
```

- [ ] **Step 3: Commit**

```bash
git add monitored-app/
git commit -m "chore: scaffold monitored-app project"
```

---

### Task 2: Flask 应用骨架 + 用户模型

**Files:**
- Create: `monitored-app/app.py` (line 1–80)

- [ ] **Step 1: Write app.py — 应用初始化 + 数据库 + 种子路由**

```python
import sqlite3
import random
import time
import requests
from threading import Thread
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
```

- [ ] **Step 2: Write seed.py**

```python
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
            pass  # 已存在则跳过

    conn.commit()
    conn.close()
    print("Seeded 5 users.")


if __name__ == "__main__":
    seed()
```

- [ ] **Step 3: 在 app.py 末尾添加启动代码**

```python
if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
```

- [ ] **Step 4: 验证启动**

```bash
cd monitored-app
pip install -r requirements.txt
python seed.py
python app.py
```

访问 `http://localhost:5000`，预期看到页面正常加载（即使模板还没写，会报 500，但启动不报错即为成功）。

- [ ] **Step 5: Commit**

```bash
git add monitored-app/
git commit -m "feat: Flask app skeleton with SQLite user model"
```

---

### Task 3: 登录功能 + 欢迎页

**Files:**
- Modify: `monitored-app/app.py`
- Create: `monitored-app/templates/index.html`
- Create: `monitored-app/templates/welcome.html`

- [ ] **Step 1: 添加登录路由到 app.py**

```python
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
            return redirect(f"/welcome?username={username}")
        else:
            error = "用户名或密码错误"

    return render_template("index.html", error=error)
```

- [ ] **Step 2: 添加 welcome 路由**

```python
@app.route("/welcome")
def welcome():
    username = request.args.get("username", "用户")
    return render_template("welcome.html", username=username)
```

- [ ] **Step 3: 写 templates/welcome.html**

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <title>欢迎</title>
  <style>
    body { font-family: system-ui; display: flex; align-items: center; justify-content: center; min-height: 100vh; margin: 0; background: #f3f4f6; }
    .card { background: white; padding: 48px; border-radius: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); text-align: center; }
    h1 { font-size: 24px; color: #111827; margin-bottom: 24px; }
    a { color: #6b7280; text-decoration: none; }
    a:hover { color: #111827; }
  </style>
</head>
<body>
  <div class="card">
    <h1>欢迎，{{ username }}！</h1>
    <a href="/">← 返回登录页</a>
  </div>
</body>
</html>
```

- [ ] **Step 4: 验证手动启动 + 访问测试**

```bash
python app.py
```

浏览器访问 `http://localhost:5000`，用 zhangsan / 123456 登录，应跳转到欢迎页。

- [ ] **Step 5: Commit**

```bash
git add monitored-app/
git commit -m "feat: login and welcome routes"
```

---

### Task 4: 登录页模板（含配置 + 模拟按钮 + 日志区）

**Files:**
- Create: `monitored-app/templates/index.html`

- [ ] **Step 1: 写 templates/index.html**

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>校园系统模拟器</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: system-ui; background: #f3f4f6; display: flex; justify-content: center; padding: 40px 16px; }
    .container { width: 100%; max-width: 480px; display: flex; flex-direction: column; gap: 24px; }
    .card { background: white; border-radius: 16px; padding: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
    h1 { font-size: 20px; font-weight: 600; color: #111827; margin-bottom: 20px; }
    .section-label { font-size: 12px; font-weight: 500; color: #9ca3af; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 12px; }
    .form-group { margin-bottom: 16px; }
    label { display: block; font-size: 14px; font-weight: 500; color: #374151; margin-bottom: 6px; }
    input { width: 100%; height: 40px; padding: 0 12px; border: 1px solid #e5e7eb; border-radius: 8px; font-size: 14px; outline: none; }
    input:focus { border-color: #111827; box-shadow: 0 0 0 3px rgba(17,24,39,0.1); }
    .btn { width: 100%; height: 40px; border: none; border-radius: 8px; font-size: 14px; font-weight: 500; cursor: pointer; transition: all 0.2s; }
    .btn-primary { background: #111827; color: white; }
    .btn-primary:hover { background: #374151; }
    .btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
    .btn-outline { background: transparent; color: #374151; border: 1px solid #e5e7eb; }
    .btn-outline:hover { background: #f9fafb; }
    .btn-outline:disabled { opacity: 0.5; cursor: not-allowed; }
    .btn-danger { background: #ef4444; color: white; }
    .btn-danger:hover { background: #dc2626; }
    .btn-danger:disabled { opacity: 0.5; cursor: not-allowed; }
    .error-msg { color: #ef4444; font-size: 14px; margin-top: 8px; }
    .btn + .btn { margin-top: 8px; }
    .log-area { background: #111827; color: #22c55e; font-family: 'Cascadia Code', 'Fira Code', monospace; font-size: 12px; padding: 16px; border-radius: 8px; height: 160px; overflow-y: auto; line-height: 1.6; }
    .log-area .dim { color: #6b7280; }
    .separator { border: none; border-top: 1px solid #e5e7eb; margin: 16px 0; }
    .inline-flex { display: flex; gap: 8px; }
    .inline-flex .btn { flex: 1; }
  </style>
</head>
<body>
  <div class="container">
    <!-- 登录卡片 -->
    <div class="card">
      <h1>校园系统模拟器</h1>
      <form method="POST" action="/">
        <div class="form-group">
          <label for="username">用户名</label>
          <input id="username" name="username" placeholder="输入用户名" required>
        </div>
        <div class="form-group">
          <label for="password">密码</label>
          <input id="password" name="password" type="password" placeholder="输入密码" required>
        </div>
        {% if error %}
          <div class="error-msg">{{ error }}</div>
        {% endif %}
        <button type="submit" class="btn btn-primary">登录</button>
      </form>
    </div>

    <!-- 演示卡片 -->
    <div class="card">
      <div class="section-label">演示</div>
      <div class="inline-flex">
        <button class="btn btn-danger" onclick="simulate('frequency')" id="btn-freq">模拟频率异常 ×10</button>
        <button class="btn btn-danger" onclick="simulate('device')" id="btn-device">模拟设备异常</button>
      </div>
    </div>

    <!-- 配置卡片 -->
    <div class="card">
      <div class="section-label">配置</div>
      <div class="form-group">
        <label for="platform-url">平台地址</label>
        <input id="platform-url" value="http://localhost:8001" placeholder="http://localhost:8001">
      </div>
      <div class="form-group">
        <label for="api-key">API Key</label>
        <input id="api-key" value="dev-api-key-change-in-production" placeholder="API Key">
      </div>
    </div>

    <!-- 日志卡片 -->
    <div class="card">
      <div class="section-label">日志</div>
      <div class="log-area" id="log-area">> 就绪</div>
    </div>
  </div>

  <script>
    function log(msg, dim) {
      const el = document.getElementById('log-area');
      const line = document.createElement('div');
      line.textContent = `> ${new Date().toLocaleTimeString()} ${msg}`;
      if (dim) line.className = 'dim';
      el.appendChild(line);
      el.scrollTop = el.scrollHeight;
    }

    function getConfig() {
      return {
        platform_url: document.getElementById('platform-url').value || 'http://localhost:8001',
        api_key: document.getElementById('api-key').value || 'dev-api-key-change-in-production',
      };
    }

    async function simulate(type) {
      const btn = document.getElementById(type === 'frequency' ? 'btn-freq' : 'btn-device');
      btn.disabled = true;
      log(`开始模拟: ${type === 'frequency' ? '频率异常' : '设备异常'}...`);

      try {
        const resp = await fetch('/api/simulate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ type, ...getConfig() }),
        });
        const result = await resp.json();
        result.logs.forEach(l => log(l.msg, l.dim));
      } catch (err) {
        log(`请求失败: ${err.message}`);
      } finally {
        btn.disabled = false;
      }
    }
  </script>
</body>
</html>
```

- [ ] **Step 2: Commit**

```bash
git add monitored-app/
git commit -m "feat: login page with config, simulation buttons, and log area"
```

---

### Task 5: 上报逻辑

**Files:**
- Modify: `monitored-app/app.py`

- [ ] **Step 1: 添加 import 和上报函数**

在 `app.py` 文件顶部已有的 `import` 后面追加：

```python
import hashlib
from datetime import datetime, timezone
```

在 `init_db()` 之后添加：

```python
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
```

- [ ] **Step 2: 在 login 路由中 `if user:` 后加上报逻辑**

将 `if user:` 块改为：

```python
        if user:
            log_data = {
                "username": username,
                "login_time": datetime.now(timezone.utc).isoformat(),
                "ip_address": request.remote_addr or "127.0.0.1",
                "user_agent": request.headers.get("User-Agent", "Unknown"),
                "login_status": "success",
            }
            report_log(log_data, request.form.get("platform_url", "http://localhost:8001"),
                       request.form.get("api_key", "dev-api-key-change-in-production"))
            return redirect(f"/welcome?username={username}")
```

对应地，在 `index.html` 的登录 form 内添加两个隐藏字段：

```html
<input type="hidden" name="platform_url" id="hf-url" value="http://localhost:8001">
<input type="hidden" name="api_key" id="hf-key" value="dev-api-key-change-in-production">
```

并在前端 JS 的 `getConfig` 函数执行时同步更新 hidden input。或者在 login form 提交前更新：

```html
<form method="POST" action="/" onsubmit="syncConfig()">
```

```js
function syncConfig() {
  document.getElementById('hf-url').value = document.getElementById('platform-url').value;
  document.getElementById('hf-key').value = document.getElementById('api-key').value;
}
```

- [ ] **Step 3: Commit**

```bash
git add monitored-app/
git commit -m "feat: report login to monitoring platform"
```

---

### Task 6: 模拟频率异常 ×10

**Files:**
- Modify: `monitored-app/app.py`

- [ ] **Step 1: 添加模拟路由到 app.py**

```python
@app.route("/api/simulate", methods=["POST"])
def simulate():
    body = request.get_json()
    sim_type = body.get("type")
    platform_url = body.get("platform_url", "http://localhost:8001")
    api_key = body.get("api_key", "dev-api-key-change-in-production")
    logs = []

    if sim_type == "frequency":
        for i in range(10):
            data = {
                "username": "zhaoliu",
                "login_time": datetime.now(timezone.utc).isoformat(),
                "ip_address": f"192.168.1.{random.randint(100, 200)}",
                "user_agent": "Mozilla/5.0 (Windows NT 10.0)",
                "login_status": "failed",
            }
            ok = report_log(data, platform_url, api_key)
            status = "✓" if ok else "✗"
            logs.append({"msg": f"[{status}] 频率 {i+1}/10  zhaoliu  {data['ip_address']}", "dim": True})
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
```

- [ ] **Step 2: 验证模拟功能**

启动 `python app.py`，浏览器打开，点击 `模拟频率异常 ×10`，观察日志区实时输出。整个过程约 80-120 秒。

然后切到监控平台（http://localhost:8001 或 localhost:8080），查看告警列表，应出现 `frequency` 告警。

- [ ] **Step 3: Commit**

```bash
git add monitored-app/
git commit -m "feat: simulate frequency and device anomaly"
```

---

### Task 7: 登录时同时上报失败日志

**Files:**
- Modify: `monitored-app/app.py`

- [ ] **Step 1: 在 login 路由中失败路径也上报**

将 `else:` 块改为：

```python
        else:
            error = "用户名或密码错误"
            log_data = {
                "username": username,
                "login_time": datetime.now(timezone.utc).isoformat(),
                "ip_address": request.remote_addr or "127.0.0.1",
                "user_agent": request.headers.get("User-Agent", "Unknown"),
                "login_status": "failed",
            }
            report_log(log_data, request.form.get("platform_url", "http://localhost:8001"),
                       request.form.get("api_key", "dev-api-key-change-in-production"))
```

- [ ] **Step 2: Commit**

```bash
git add monitored-app/
git commit -m "feat: report failed login attempts to platform"
```

---

### Task 8: 验证全流程

- [ ] **Step 1: 验证启动**

```bash
cd monitored-app
pip install -r requirements.txt
python seed.py
python app.py
```

访问 `http://localhost:5000`，确认页面正常加载。

- [ ] **Step 2: 验证真实登录上报**

用 `zhangsan` / `123456` 登录，登录后刷新监控平台前端或查日志，确认出现一条 `success` 日志。

- [ ] **Step 3: 验证失败登录上报**

用错误密码试一次，确认监控平台收到一条 `failed` 日志。

- [ ] **Step 4: 验证频率异常模拟**

点 `模拟频率异常 ×10`，等待完成后，到监控平台查看告警列表是否出现 `frequency` 告警。

- [ ] **Step 5: 验证设备异常模拟**

点 `模拟设备异常`，到监控平台查看是否出现 `device` 告警。

- [ ] **Step 6: 更新 README**

在项目根 README.md 中补充被监控方使用说明。
