# 任务

## 任务名称

第2周：管理员认证

## 任务描述

实现管理员登录认证系统，使管理员可以登录本监测平台。

详见 [规划文档](../../../.planning/2-PLAN.md)

## 拆解步骤

1. 创建 JWT 依赖注入（`app/core/deps.py`）
2. 创建认证路由（`app/api/auth.py`）
3. 注册路由到 main.py
4. 创建 Seed 脚本（`backend/scripts/seed.py`）
5. 更新 Token 过期时间为 24 小时
6. 前端 Login.vue 对接真实 API
7. 前端路由守卫

## 预期结果

- 管理员可登录并获取 JWT token
- 已登录管理员可创建新管理员
- 种子脚本可初始化默认管理员
- 前端登录页可正常登录
- 未登录自动跳转登录页

## 实际验证结果

### ✅ 验证通过

| 测试场景 | 结果 |
|---------|------|
| 登录成功返回 token | 200, token 正确 |
| 错误密码返回 401 | 401, "用户名或密码错误" |
| 无 token 访问受保护接口 | 401, "未提供认证凭证" |
| 获取当前用户信息 | 200, 返回 username=admin, role=admin |
| 已登录管理员创建新管理员 | 200, 新管理员创建成功 |
| 重复用户名注册 | 400, "用户名已存在" |
| 无 token 注册 | 401, "未提供认证凭证" |
| Seed 脚本（幂等） | 已存在则跳过，不重复创建 |
| 现有 pytest 测试 | 3/3 passed |

### 📁 新增/修改文件

| 文件 | 变更 |
|------|------|
| `backend/app/core/deps.py` | 新增 - JWT 依赖注入 |
| `backend/app/core/config.py` | 修改 - ACCESS_TOKEN_EXPIRE_MINUTES=1440 |
| `backend/app/api/auth.py` | 新增 - 登录/注册/me 端点 |
| `backend/app/main.py` | 修改 - 注册 auth 路由 |
| `backend/scripts/seed.py` | 新增 - 管理员初始化脚本 |
| `frontend/src/views/Login.vue` | 修改 - 对接真实 API |
| `frontend/src/router/index.js` | 修改 - 添加 beforeEach 路由守卫 |