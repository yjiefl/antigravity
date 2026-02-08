# 计划管理系统 (Plan Management System)

适配企业组织架构、覆盖任务全生命周期的轻量级管理工具。

## 技术栈

- **前端**: Vue 3 + Vite + Tailwind CSS + Pinia
- **后端**: Python 3.11+ FastAPI + SQLAlchemy 2.0
- **数据库**: PostgreSQL 15+
- **缓存**: Redis 7+
- **部署**: Docker Compose

## 快速开始

### 开发环境

```bash
# 1. 启动数据库和 Redis
docker-compose up -d db redis

# 2. 启动后端
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# 3. 启动前端
cd frontend
npm install
npm run dev
```

### Docker 部署

```bash
docker-compose up -d
```

访问地址：

- 前端: <http://localhost:5173>
- 后端 API: <http://localhost:8000>
- API 文档: <http://localhost:8000/api/docs>

## 初始账户

首次启动需要创建管理员账户。可通过 API 或数据库直接创建：

```sql
INSERT INTO users (id, username, password_hash, real_name, role, is_active)
VALUES (gen_random_uuid(), 'admin', '$2b$12$xxxxx', '管理员', 'admin', true);
```

## 目录结构

```
计划管理系统/
├── backend/          # 后端代码
│   ├── app/
│   │   ├── api/      # API 路由
│   │   ├── core/     # 配置、数据库
│   │   ├── models/   # 数据模型
│   │   ├── schemas/  # Pydantic 模式
│   │   └── services/ # 业务服务
│   └── tests/
├── frontend/         # 前端代码
│   └── src/
│       ├── api/      # API 客户端
│       ├── components/
│       ├── views/    # 页面组件
│       ├── stores/   # Pinia 状态
│       └── router/
├── docker-compose.yml
├── spec.md           # 技术规格
└── plan.md           # 需求文档
```

## 许可证

MIT
