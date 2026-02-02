# 储能自动调节系统

光储电站储能AGC有功控制系统 - 根据调度指令自动计算储能调节策略

## 功能特点

- ⚡ **智能调节计算** - 根据调度AGC指令、光伏出力、储能状态自动计算调节策略
- 📊 **特征码系统** - 四维条件判断，精确确定调节方向
- 🔔 **告警提示** - SOC边界、AGC限制等场景自动告警
- 📝 **历史记录** - 自动保存计算历史，支持回溯分析

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vite + React |
| 后端 | Python FastAPI |
| 数据库 | SQLite |

## 快速开始

### 1. 启动后端

```bash
cd backend
pip3 install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 2. 启动前端

```bash
cd frontend
npm install
npm run dev
```

### 3. 访问应用

打开浏览器访问 <http://localhost:5173>

## 核心公式

```
总有功 = 光伏出力 + 储能出力
储能调节目标 = 调度指令值 - 光伏出力
```

## API接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/v1/calculate | 计算调节策略 |
| GET | /api/v1/history | 获取历史记录 |
| GET | /api/v1/config | 获取配置 |
| PUT | /api/v1/config | 更新配置 |

## 项目结构

```
储能自动调节系统/
├── backend/                # 后端代码
│   ├── app/
│   │   ├── main.py        # FastAPI入口
│   │   ├── models/        # 数据模型
│   │   ├── services/      # 业务逻辑
│   │   ├── routers/       # API路由
│   │   └── database/      # 数据库
│   └── tests/             # 单元测试
├── frontend/              # 前端代码
│   └── src/
│       ├── App.jsx        # 主应用
│       └── components/    # 组件
├── spec.md                # 规格说明
├── guide.md               # 使用指南
└── readme.md              # 本文件
```

## 许可证

MIT
