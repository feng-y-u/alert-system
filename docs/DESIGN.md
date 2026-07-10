# 详细设计方案

**校园账号异常登录监测与告警平台** — 详细设计文档

> 核心框架信息（技术栈、项目结构、命令等）请参考 [CLAUDE.md](../CLAUDE.md)  
> UI 设计规范请参考 [UI.md](UI.md)

---

## 项目定位

监控/运维类平台，接收校园系统的登录日志，检测异常登录行为并产生告警，供管理员处理。

```
校园系统（被监控） → POST /api/logs → 本平台 → 检测异常 → 告警 → 管理员处理
```

| 角色 | 说明 |
|------|------|
| **管理员** | 使用本平台的人，登录后查看 Dashboard、日志、告警，并进行处理 |
| **校园系统用户** | 被监控系统的使用者（学生/教师），**不是本项目的用户**，他们的登录行为是监控数据来源 |

---

## 数据模型

### users（管理员表）
```
id, username, email, hashed_password, role(admin), is_active, created_at, updated_at
```

### login_logs（登录日志表）
```
id, username(被监控用户), login_time, ip_address, user_agent, login_status, location, created_at, updated_at
```

### alerts（告警表）
```
id, username(关联login_logs), alert_type(frequency/device/location), alert_message,
severity(low/medium/high), status(pending/acknowledged/resolved), created_at, updated_at, resolved_at
```

---

## 开发计划（8周）

| 周次 | 内容 | 状态 |
|------|------|------|
| 第1周 | 项目搭建：FastAPI框架 + MySQL/Redis + 基础模型 + Vue 3 + Docker | ✅ |
| 第2周 | 管理员认证：登录/注册 JWT API + seed 脚本 + 前端登录页 + 路由守卫 | ✅ |
| 第3周 | 登录日志管理：接收/查询 API + 模拟数据脚本 | ✅ |
| 第4周 | 异常检测：频率异常 + 设备异常 + Pandas 分析 | ⏳ 当前进行 |
| 第5周 | 告警系统：生成/查询 API + 邮件通知 | ❌ |
| 第6周 | 前端页面联调：日志列表 + 告警列表 + ECharts 图表 | ❌ |
| 第7周 | 功能完善：实时通知 + 优化 + 错误处理 | ❌ |
| 第8周 | 测试与部署：集成测试 + Docker 部署 + 文档 | ❌ |

### 后续扩展
地理位置检测（IP库）、WebSocket 实时监控、告警规则配置界面、移动端适配

---

## 项目结构

```
backend/
├── app/
│   ├── api/           # API 路由（每个功能一个文件）
│   ├── core/          # 配置 + 数据库 + 安全 + 依赖注入
│   ├── models/        # SQLAlchemy ORM 模型
│   ├── schemas/       # Pydantic 请求/响应模式
│   ├── services/      # 业务逻辑
│   └── tasks/         # Celery 异步任务
├── alembic/           # 数据库迁移
├── tests/             # pytest 测试
├── scripts/           # 工具脚本（如 seed.py）
└── requirements.txt
frontend/
├── src/
│   ├── api/           # Axios 客户端
│   ├── layouts/       # 布局组件
│   ├── router/        # 路由配置
│   ├── stores/        # Pinia 状态管理
│   ├── views/         # 页面视图
│   └── components/    # Vue 组件
└── ...
```


## 注意事项

1. **角色区分** — 不要混淆"被监控用户"和"本平台管理员"
2. **数据隐私** — 登录日志含敏感信息，确保加密传输和存储
3. **异步处理** — 耗时操作（邮件、检测）使用 Celery 异步执行
4. **性能** — Pandas 分析大量日志时优先使用数据库查询优化