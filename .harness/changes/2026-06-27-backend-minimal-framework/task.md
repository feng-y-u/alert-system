# 任务模板

## 任务名称

搭建后端FastAPI项目框架（最小可行版本）

## 任务描述

搭建一个最小可行的FastAPI后端框架，能启动服务、响应健康检查请求，并为后续功能扩展提供标准化的模块化结构。

## 拆解步骤

1. 创建 backend/ 目录结构
2. 编写 app/main.py（应用入口，组装中间件和路由）
3. 编写 app/api/health.py（健康检查端点）
4. 编写 requirements.txt（依赖文件）
5. 验证服务启动和端点响应

## 预期结果

- 服务能正常启动，监听 0.0.0.0:8000
- `GET /api/health` 返回 `{"status":"ok","message":"服务运行正常"}`
- 访问 `http://localhost:8000/docs` 显示 Swagger API 文档
- CORS 配置允许前端跨域请求

## 实际验证结果

