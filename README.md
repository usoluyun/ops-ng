# ops-ng

现代化运维工具系统，基于 Next.js + FastAPI + Strapi 架构。

## 架构

```
┌─────────────────────────────────────┐
│        客户端 (UI / Mobile)          │
└─────────────────────────────────────┘
              ↓         ↓
    ┌─────────────────┬────────────────┐
    ↓                 ↓                ↓
ORY Hydra      Login App(FastAPI) BBF(FastAPI)
(OAuth2)       (登录页)          (路由)
    ↑             ↑                ↑
    └─────────────┴────────────────┘
                  ↓
           Strapi 5 + PostgreSQL
                  ↓
           Agent (LangChain + Dramatiq)
                  ↓
           Redis (队列 + 缓存)
```

## 技术栈

| 组件 | 技术选型 |
|------|---------|
| OAuth2 | ORY Hydra |
| 登录服务 | FastAPI |
| API 网关 | FastAPI BBF |
| 主数据 | Strapi 5 + PostgreSQL |
| Agent | LangChain + LangGraph + Dramatiq |
| 任务队列 | Dramatiq + Redis |
| 前端 | Next.js + shadcn/ui |

## 文档

- [架构文档](doc/architecture-v2.md)

## 开发

### 前置要求

- Node.js 18+
- Python 3.11+
- PostgreSQL 15+
- Redis 7+

### 快速开始

```bash
# 克隆项目
git clone https://github.com/your-org/ops-ng.git
cd ops-ng

# 启动基础设施
docker-compose up -d postgres redis

# 启动 Strapi
cd strapi && npm install && npm run develop

# 启动 BBF
cd bbf && pip install -r requirements.txt && uvicorn main:app --reload

# 启动 Login App
cd login-app && pip install -r requirements.txt && uvicorn main:app --reload
```

## 项目结构

```
ops-ng/
├── doc/              # 架构文档
├── frontend/         # Next.js 前端 (规划中)
├── bbf/              # FastAPI BBF 网关 (规划中)
├── login-app/        # FastAPI 登录服务 (规划中)
├── strapi/           # Strapi 主数据服务 (规划中)
├── agent/            # Agent 服务 (规划中)
└── legacy/           # 旧系统 (ASP.NET MVC)
```

## 许可

MIT
