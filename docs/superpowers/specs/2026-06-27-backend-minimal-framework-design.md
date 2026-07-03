# 后端最小框架设计

**日期**：2026-06-27
**状态**：已批准
**范围**：第1周任务 - 搭建后端FastAPI项目框架

---

## 目标

搭建一个最小可行的FastAPI后端框架，能启动服务、响应健康检查请求，并为后续功能扩展提供标准化的模块化结构。

## 验收标准

- [ ] 服务能正常启动，监听 0.0.0.0:8000
- [ ] `GET /api/health` 返回 `{"status":"ok","message":"服务运行正常"}`
- [ ] 访问 `http://localhost:8000/docs` 显示 Swagger API 文档
- [ ] CORS 配置允许前端跨域请求
- [ ] 项目结构符合模块化规范

## 技术选型

| 组件 | 版本 | 用途 |
|------|------|------|
| FastAPI | 0.104.1 | Web框架 |
| uvicorn | 0.24.0 | ASGI服务器 |

## 目录结构

```
backend/
├── app/
│   ├── __init__.py           # 包标记
│   ├── main.py               # 应用入口，组装中间件和路由
│   └── api/
│       ├── __init__.py
│       └── health.py         # 健康检查端点
├── requirements.txt
└── README.md
```

## 核心代码设计

### app/main.py

职责：应用入口，只做组装，不写业务逻辑。

- 创建 FastAPI 实例，配置标题、描述、版本
- 添加 CORS 中间件，allow_origins=["*"]
- 注册 health 路由，prefix="/api"

### app/api/health.py

职责：健康检查端点，独立模块。

- 定义 router = APIRouter()
- GET /health → 返回 {"status": "ok", "message": "服务运行正常"}

## 运行方式

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 验证方式

| 验证项 | 方法 | 预期结果 |
|--------|------|----------|
| 服务启动 | 终端输出 | Uvicorn running on http://0.0.0.0:8000 |
| 健康检查 | curl http://localhost:8000/api/health | {"status":"ok","message":"服务运行正常"} |
| API文档 | 浏览器访问 http://localhost:8000/docs | 显示 Swagger UI |
| CORS | 前端跨域请求 | 不被拦截 |

## 扩展方式

后续添加新功能模块（如 users.py、logs.py）只需两步：
1. 创建 app/api/xxx.py，定义 router
2. main.py 中 import 并 include_router

详见 [DESIGN.md - 添加新功能的方法](../DESIGN.md)
