# 被监控方模拟器设计文档

**日期：** 2026-07-15
**状态：** 设计稿

---

## 1. 背景

监控平台"校园账号异常登录监测与告警平台"已开发完成，现有的日志写入接口 `POST /api/logs` 需要手动调 HTTP 请求才能看到效果。需要一个轻量的"被监控方"模拟器，既能真实登录操作（展示完整数据流），又能一键触发异常（验证监控平台的检测能力）。

## 2. 架构

```
用户浏览器 ──→ 被监控方 (Flask :5000) ──POST /api/logs──→ 监控平台 (:8001)
                  │                         X-API-Key
              SQLite 用户表
              (预置 5 个测试账号)
```

- 被监控方**独立运行**，不依赖监控平台的数据库
- 通过 HTTP 与监控平台通信，一个请求就是一条登录日志
- 无论登录成功/失败，都上报日志（失败日志才是触发告警的关键）

## 3. 文件结构

```
monitored-app/
├── app.py               # Flask 入口，路由 + 数据库 + 上报逻辑
├── templates/
│   └── index.html       # 登录页（含配置区 + 模拟按钮）
├── templates/
│   └── welcome.html     # 登录成功欢迎页
├── seed.py              # 初始化预置用户
└── requirements.txt     # flask, requests
```

## 4. 预置用户

| 用户名 | 密码 | 角色 | 说明 |
|--------|------|------|------|
| zhangsan | 123456 | 学生 | 正常用户 |
| lisi | 123456 | 学生 | 用于频率异常的触发用户 |
| wangwu | 123456 | 学生 | 用于设备异常的触发用户 |
| zhaoliu | 123456 | 学生 | 暴力破解测试 |
| admin | admin123 | 管理员 | 管理员账号 |

## 5. 页面设计

### 5.1 登录页（`/`）

```
┌─────────────────────────────┐
│  校园系统模拟器              │
│                             │
│  用户名  [______________]   │
│  密码    [______________]   │
│                             │
│  [   登录   ]               │
│                             │
│  ──── 演示 ────             │
│  [ 模拟频率异常 ×10 ]       │
│  [ 模拟设备异常 ]           │
│                             │
│  ──── 配置 ────             │
│  平台地址  [http://localhost]│
│  API Key  [dev-...        ] │
│                             │
│  ──── 日志 ────             │
│  > 15:30:22 登录成功: ...   │
│  > 15:30:25 已上报: ...     │
└─────────────────────────────┘
```

- 登录成功 → 跳转 `/welcome?username=xxx`
- 登录失败 → 页面显示错误消息（不清空表单）
- 所有模拟/登录操作的结果实时显示在底部日志区

### 5.2 欢迎页（`/welcome`）

简单显示 "欢迎，xxx！" + 返回登录页的链接。

## 6. 模拟功能

### 6.1 模拟频率异常

- 按钮：`模拟频率异常 ×10`
- 使用用户：`zhaoliu`
- 行为：循环 10 次 POST 日志到监控平台，`login_status: "failed"`
  - `ip_address` 在 `192.168.1.100-200` 范围内随机
  - `user_agent` 固定为 `Mozilla/5.0 (Windows NT 10.0)`
  - 每次间隔 8-12 秒（后端 `time.sleep`），总耗时约 90 秒
- 预期效果：监控平台触发 `frequency` 告警（medium）

### 6.2 模拟设备异常

- 按钮：`模拟设备异常`
- 使用用户：`wangwu`
- 行为：同时 POST 3 条日志（不间隔），分别使用不同设备组合：

| 序号 | user_agent | ip_address |
|------|-----------|-----------|
| 1 | `Mozilla/5.0 (Windows NT 10.0)` | `192.168.1.10` |
| 2 | `Mozilla/5.0 (iPhone; CPU iPhone OS 17_0)` | `10.0.0.20` |
| 3 | `Mozilla/5.0 (Linux; Android 14)` | `172.16.0.30` |

- 预期效果：监控平台触发 `device` 告警（high）

## 7. 日志上报

Flask 后端接收模拟请求时，从请求 body 中拿到 `platform_url` 和 `api_key`，然后循环 POST 到监控平台：

```python
def report_log(data: dict, platform_url: str, api_key: str):
    resp = requests.post(
        platform_url + "/api/logs",
        json=data,
        headers={"X-API-Key": api_key},
        timeout=5,
    )
    return resp.status_code == 201
```

- 超时 5 秒
- 失败不重试（日志记到 UI 即可，不影响主流程）

## 8. 配置

配置区放在登录页底部，通过浏览器 `localStorage` 持久化。

**关键设计：** 模拟请求由前端发起，前端把配置连同请求类型一起 POST 给 Flask 后端，后端拿到配置后再上报到监控平台。

```python
# 前端 → Flask
POST /api/simulate/frequency
Body: { "platform_url": "...", "api_key": "..." }

# Flask → 监控平台
POST {platform_url}/api/logs
Headers: { "X-API-Key": {api_key} }
```

两种模拟共用同一个 `/api/simulate` 端点，通过 `type` 参数区分：

| 请求 | Body |
|------|------|
| `POST /api/simulate` | `{ "type": "frequency", "platform_url": "...", "api_key": "..." }` |
| `POST /api/simulate` | `{ "type": "device", "platform_url": "...", "api_key": "..." }` |

**默认值：**
- 平台地址 — `http://localhost:8001`（Docker 部署时为 `http://localhost`）
- API Key — `dev-api-key-change-in-production`

## 9. 启动方式

```bash
cd monitored-app
pip install -r requirements.txt
python seed.py              # 初始化 5 个用户
python app.py               # 启动 :5000
```

浏览器访问 `http://localhost:5000`。

## 10. 与现有系统关系

- 被监控方**完全独立**，单独目录、单独依赖
- 唯一耦合点是 `POST /api/logs` 接口的请求格式（`LoginLogCreate` schema）
- 不引入任何监控平台的代码依赖
