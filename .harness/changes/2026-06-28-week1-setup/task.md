# 任务模板

## 任务名称

第1周：项目搭建与基础架构

## 任务描述

按照DESIGN.md第1周计划，完成以下任务：
1. 搭建后端FastAPI项目框架（已完成）
2. 配置MySQL和Redis（数据库连接配置）
3. 创建基础数据库模型（SQLAlchemy模型）
4. 搭建Vue 3项目框架
5. 配置Docker Compose开发环境

## 拆解步骤

### 1. 配置MySQL和Redis
- 在requirements.txt中添加sqlalchemy、pymysql、alembic、redis等依赖
- 创建backend/app/core/config.py（Pydantic Settings配置）
- 创建backend/app/core/database.py（SQLAlchemy数据库连接）
- 创建backend/.env.example（环境变量示例）

### 2. 创建基础数据库模型
- 创建backend/app/models/目录
- 创建backend/app/models/user.py（用户表）
- 创建backend/app/models/login_log.py（登录日志表）
- 创建backend/app/models/alert.py（告警表）
- 创建backend/app/schemas/目录（Pydantic数据模式）

### 3. 搭建Vue 3项目框架
- 使用npm create vue@latest创建前端项目
- 安装Element Plus、Axios、Vue Router、Pinia
- 配置基础路由和页面结构

### 4. 配置Docker Compose
- 创建docker-compose.yml（MySQL + Redis + 后端服务）
- 创建backend/Dockerfile
- 创建.env文件（环境变量）
- 验证docker-compose up能正常启动

## 预期结果

- 后端能连接MySQL和数据库迁移正常
- Redis连接正常
- 数据库模型能通过Alembic生成迁移
- 前端项目能正常启动
- docker-compose up能启动所有服务

## 实际验证结果

### ✅ 已完成
1. **后端核心配置**：config.py、database.py、redis.py 已创建
2. **数据库模型**：User、LoginLog、Alert 三个模型已创建
3. **Alembic迁移**：alembic.ini 和 env.py 已配置，初始迁移已生成（59f48e69b011）
4. **Docker配置**：docker-compose.yml 和 Dockerfile 已创建
5. **Vue 3前端**：项目结构、路由、API客户端、基础页面已创建

### ✅ 第1周补全项
1. **安全工具模块**：backend/app/core/security.py（passlib 密码哈希 + JWT 生成/验证）
2. **Celery 应用**：backend/app/tasks/__init__.py（Celery 应用对象）+ email.py + detection.py（占位任务）
3. **Pydantic Schemas**：backend/app/schemas/user.py、login_log.py、alert.py
4. **测试基础设施**：backend/tests/conftest.py、test_health.py、test_security.py
   - pytest 3 tests passed
5. **前端布局组件**：frontend/src/layouts/MainLayout.vue（侧边栏 + 顶栏 + 导航菜单）
6. **Pinia 认证 Store**：frontend/src/stores/auth.js（login/logout/token管理）
7. **增强 Dashboard**：接入 ECharts 折线图占位 + 响应式统计卡片
8. **整合路由**：router/index.js 使用 MainLayout 作为父路由
9. **ESLint 配置**：frontend/.eslintrc.cjs
10. **Black 配置**：backend/pyproject.toml
11. **README.md**：项目根目录 README.md
12. **依赖版本修复**：requirements.txt 新增 bcrypt==4.0.1、httpx==0.27.2

### ⚠️ 待解决
- Docker 镜像源配置问题（需修复后才能启动 MySQL/Redis 容器）
- pandas 在 Python 3.13 上编译失败（mesonpy 兼容性问题），待用 `--only-binary :all: pandas` 安装或降级 Python

### 📁 新增/修改文件清单
- backend/app/core/security.py (新)
- backend/app/tasks/__init__.py (改写)
- backend/app/tasks/email.py (新)
- backend/app/tasks/detection.py (新)
- backend/app/schemas/user.py (新)
- backend/app/schemas/login_log.py (新)
- backend/app/schemas/alert.py (新)
- backend/tests/conftest.py (新)
- backend/tests/test_health.py (新)
- backend/tests/test_security.py (新)
- backend/pyproject.toml (新)
- backend/requirements.txt (修改)
- frontend/src/layouts/MainLayout.vue (新)
- frontend/src/stores/auth.js (新)
- frontend/src/router/index.js (修改)
- frontend/src/views/Dashboard.vue (修改)
- frontend/.eslintrc.cjs (新)
- README.md (新)