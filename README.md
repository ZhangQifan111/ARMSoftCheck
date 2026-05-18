# 评审前风险自检系统 (PRRC)

Pre-Review Risk Checklist System

## 概述

嵌入式团队代码评审前的风险自检工具。开发在提交评审前填写自检单，系统根据改动模块自动生成测试项，逐项填写后提交，评审人审核通过方可合入。全链路记录可查询。

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue3 + TypeScript + Vite + Element Plus + Pinia + Axios |
| 后端 | FastAPI + SQLAlchemy 2.0 + Pydantic + Alembic + JWT |
| 数据库 | MySQL 8 |
| 部署 | Docker Compose + Nginx |

## 快速启动

### 1. 仅启动（使用 seed 数据自动导入）

```bash
cd prrc-system
docker-compose up -d
```

访问 http://localhost

### 2. 首次部署（初始化数据库 + 导入种子数据）

```bash
cd prrc-system
docker-compose up -d backend mysql

# 等待 MySQL 启动（约10秒）
sleep 10

# 导入种子数据
docker exec prrc_backend python -m seeds.import_seed
```

### 3. 停止

```bash
docker-compose down
# 保留数据卷
docker-compose down -v  # 清空数据
```

## 初始账号

| 用户名 | 密码 | 角色 | 说明 |
|--------|------|------|------|
| admin | Admin@123 | 管理员 | 全部权限 |
| dev1 | Dev@123 | 开发 | 创建/提交自检单 |
| review1 | Review@123 | 评审 | 审核自检单 |
| tester1 | Test@123 | 测试 | 只读 |

## 目录结构

```
prrc-system/
├── backend/
│   ├── app/
│   │   ├── api/routers/   # API 路由
│   │   ├── core/           # 配置、安全、数据库
│   │   ├── models/         # SQLAlchemy 模型
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # 业务逻辑
│   │   └── main.py         # FastAPI 入口
│   ├── alembic/            # 数据库迁移
│   ├── seeds/              # 种子数据导入脚本
│   ├── seed_templates/     # 种子模板（缺失时自动生成）
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/            # Axios 封装 + API 方法
│   │   ├── stores/         # Pinia 状态管理
│   │   ├── router/         # Vue Router
│   │   └── views/          # 页面组件
│   ├── Dockerfile
│   └── nginx.conf
├── docker-compose.yml
├── docs/                   # 架构/接口文档
├── seeds/                  # 实际使用的种子数据
└── README.md
```

## API 基础信息

- Base URL: `/api/v1`
- 认证: `Authorization: Bearer <JWT_TOKEN>`
- 所有响应格式: `{ "code": 0, "data": {...} }` 或 `{ "code": 0, "total": N, "items": [...] }`

详见 [docs/api.md](docs/api.md)

## 自检单编号规则

`PRRC-YYYYMMDD-XXXX`，如 `PRRC-20260518-0001`，每天从 0001 递增。

## 种子数据

seed 文件放在 `backend/seeds/` 目录（容器内挂载），也可放在 `backend/seed_templates/`。

| 文件 | 用途 |
|------|------|
| projects_seed.csv | 项目/产品线 |
| risk_modules_seed.csv | 风险模块 |
| test_items_seed.csv | 测试项字典 |
| module_test_map_seed.csv | 模块→测试项映射 |
| users_seed.csv | 用户账号 |

导入幂等，重复执行不会产生重复数据。

## 本地开发

```bash
# 后端
cd backend
pip install -r requirements.txt
cp env.sample .env
# 修改 .env 中的 MYSQL_HOST=localhost
uvicorn app.main:app --reload --port 8000

# 前端
cd frontend
pnpm install
pnpm dev
```

## 环境变量说明

```env
MYSQL_HOST=mysql          # MySQL 主机
MYSQL_PORT=3306           # MySQL 端口
MYSQL_DB=prrc             # 数据库名
MYSQL_USER=prrc           # 数据库用户
MYSQL_PASSWORD=prrc123    # 数据库密码
JWT_SECRET=xxx            # JWT 密钥（生产必须修改！）
JWT_EXPIRE_MINUTES=43200  # Token 有效期（默认12小时）
SEED_DATA_PATH=/app/seeds  # 种子数据路径
```

## 权限说明

| 角色 | 可执行操作 |
|------|-----------|
| ADMIN | 全部功能 |
| DEVELOPER | 创建/编辑/提交自检单，查看本人记录 |
| REVIEWER | 审核自检单 |
| TESTER | 只读查看 |

## 端口

| 端口 | 服务 |
|------|------|
| 80 | 前端 (Nginx) |
| 8000 | 后端 API |
| 3306 | MySQL |
