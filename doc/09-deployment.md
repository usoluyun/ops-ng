# 部署配置

> 文档版本：v0.1 | 最后更新：2026-04-25 | 负责 Agent：War Machine

## 概述

本文档描述 ops-ng 系统的容器化部署方案。系统采用 Docker Compose 编排，包含 7 个容器服务（ORY Hydra、Login App、FastAPI BBF、Strapi 5、Agent Worker、PostgreSQL、Redis），通过统一的内部网络互联。外部服务（OpsService、CenterService）不在容器内，由各服务通过环境变量配置的 URL 访问。

---

## 功能说明

> 本节面向运维团队

### 功能列表

- 一键启动全部服务（`docker compose up -d`）
- 服务间通过 Docker 内部网络互联，无需暴露内部端口
- 数据持久化：PostgreSQL 和 Redis 数据通过 Named Volume 持久化存储
- 健康检查：每个关键服务配置 healthcheck，保障依赖服务就绪后再启动
- 多环境支持：通过 `.env` 文件区分开发、测试、生产环境配置

### 操作流程

**本地开发启动流程（3 步）**

1. 克隆仓库并复制环境变量配置文件
   - 克隆代码仓库到本地
   - 将 `.env.example` 复制为 `.env`

2. 配置 `.env` 中的必填变量
   - 填写数据库密码、Hydra Secret、Strapi Admin 密码等敏感配置
   - 确认外部服务地址（OpsService、CenterService）填写正确
   - 确认代理配置（HTTP_PROXY / NO_PROXY）符合当前网络环境

3. 启动所有服务
   - 执行 `docker compose up -d` 启动全部服务
   - 执行 `docker compose ps` 确认所有容器状态为 `healthy` 或 `running`

### 服务健康检查地址

| 服务 | 健康检查地址 | 说明 |
|------|------------|------|
| ORY Hydra（公开端口） | `http://localhost:4444/health/alive` | OAuth2 公开端点存活检查 |
| ORY Hydra（管理端口） | `http://localhost:4445/health/alive` | 管理 API 存活检查 |
| FastAPI BBF | `http://localhost:8000/health` | API 网关健康检查 |
| Strapi 5 | `http://localhost:1337/_health` | 内容服务健康检查 |
| Login App | `http://localhost:3000/api/health` | 登录应用健康检查 |
| PostgreSQL | `localhost:5432`（TCP） | 数据库连接检查（psql / pg_isready） |
| Redis | `localhost:6379`（TCP） | 缓存连接检查（redis-cli ping） |

### 注意事项

**服务起不来**

- 检查 `docker compose ps` 输出，确认容器状态和退出码
- 查看对应容器日志：`docker compose logs <service_name>`
- 常见原因：端口被占用（netstat 确认）、环境变量缺失、镜像拉取失败

**连不上数据库**

- 确认 PostgreSQL 容器状态为 `healthy`（healthcheck 通过）
- 检查 `DATABASE_URL` 中的主机名是否为服务名（`postgres`），不能使用 `localhost`
- 检查数据库用户名、密码、数据库名是否与 PostgreSQL 容器环境变量一致
- 执行 `docker compose exec postgres psql -U <user> -d <db>` 验证数据库可连接

**Redis 队列堵塞**

- 检查 Agent Worker 容器是否正常运行：`docker compose logs agent`
- 确认 `REDIS_URL` 配置正确，主机名使用 `redis`
- 使用 `docker compose exec redis redis-cli llen <queue_name>` 查看队列积压长度
- 重启 Agent Worker：`docker compose restart agent`

**外部服务连接失败**

- 确认 `OPS_SERVICE_URL` 和 `CHAIN_CENTER_URL` 填写正确
- 确认 `NO_PROXY` 包含 `yaduo.com` 和 `at-our.com`，内部域名不走代理
- 在容器内测试连通性：`docker compose exec bbf curl -v <OPS_SERVICE_URL>/health`
- 如需走代理访问公网，确认 `HTTP_PROXY` / `HTTPS_PROXY` 已设置为 `http://127.0.0.1:7890`

---

## 技术设计

> 本节面向开发团队

### 组件职责

| 服务 | 镜像 | 对外端口 | 说明 |
|------|------|---------|------|
| ORY Hydra | `oryd/hydra:v2` | 4444（公开）、4445（管理） | OAuth2 / OIDC 授权服务器，负责发放和验证 Token |
| Login App | 内部构建（FastAPI / Next.js） | 3000 | 登录页 + Consent 处理，调用 Strapi 验证用户凭证 |
| FastAPI BBF | 内部构建（Python 3.12） | 8000 | API 网关，负责路由、Token 鉴权、服务编排、限流 |
| Strapi 5 | 内部构建（Node.js 20） | 1337 | 主数据服务，提供 CRUD API、用户管理、权限管理 |
| Agent Worker | 内部构建（Python 3.12） | 不对外暴露 | 后台批量任务执行引擎（LangChain + LangGraph + Dramatiq） |
| PostgreSQL | `postgres:16` | 5432 | 统一数据库，所有业务数据持久化存储 |
| Redis | `redis:7-alpine` | 6379 | 缓存 + 异步任务队列 |

### 关键接口 / API

**ORY Hydra 公开端点（端口 4444）**

- `GET /oauth2/auth` — 授权请求入口
- `POST /oauth2/token` — 获取访问 Token
- `GET /oauth2/userinfo` — 获取用户信息
- `POST /oauth2/revoke` — 撤销 Token
- `GET /.well-known/openid-configuration` — OIDC 发现文档

**ORY Hydra 管理端点（端口 4445）**

- `PUT /admin/oauth2/auth/requests/login/accept` — 接受登录请求
- `PUT /admin/oauth2/auth/requests/consent/accept` — 接受 Consent 请求
- `GET /admin/oauth2/introspect` — Token 内省

**FastAPI BBF（端口 8000）**

- `GET /health` — 健康检查
- `POST /api/v1/*` — 业务 API 路由（转发至 Strapi 或 Agent）

**Strapi 5（端口 1337）**

- `GET /_health` — 健康检查
- `POST /api/auth/local` — 用户登录验证（供 Login App 调用）
- `GET|POST|PUT|DELETE /api/*` — 业务数据 CRUD API

### 数据流

```mermaid
flowchart TD
    Client["客户端 (UI / Mobile)"] -->|OAuth2 授权码流程| Hydra["ORY Hydra\n:4444"]
    Hydra -->|Login Challenge 回调| LoginApp["Login App\n:3000"]
    LoginApp -->|验证用户凭证| Strapi["Strapi 5\n:1337"]
    Strapi --> Postgres[("PostgreSQL\n:5432")]

    Client -->|携带 Token 请求 API| BBF["FastAPI BBF\n:8000"]
    BBF -->|Token 内省| Hydra
    BBF -->|业务数据读写| Strapi
    BBF -->|投递异步任务| Redis[("Redis\n:6379")]
    Redis -->|消费任务| Agent["Agent Worker\n(Dramatiq)"]
    Agent -->|任务结果回写| Strapi
    Agent -->|调用外部服务| OpsService["OpsService\n(外部)"]
    Agent -->|调用外部服务| CenterService["CenterService SOAP\n(外部)"]

    BBF --> Redis
```

### 服务依赖关系与启动顺序

```mermaid
flowchart TD
    Postgres[("PostgreSQL\n先启动")]
    Redis[("Redis\n先启动")]

    Hydra["ORY Hydra"] -->|depends_on healthy| Postgres
    Strapi["Strapi 5"] -->|depends_on healthy| Postgres

    LoginApp["Login App"] -->|depends_on healthy| Hydra
    LoginApp -->|depends_on healthy| Strapi

    BBF["FastAPI BBF"] -->|depends_on healthy| Strapi
    BBF -->|depends_on| Redis

    Agent["Agent Worker"] -->|depends_on| Redis
    Agent -->|depends_on healthy| Strapi
```

### 依赖的外部服务

| 服务 | 协议 | 调用方 | 说明 |
|------|------|--------|------|
| OpsService | HTTP/REST | Agent Worker | 企业运维服务，域名含 `at-our.com`，不走代理 |
| CenterService | SOAP/HTTP | Agent Worker | 连锁中台服务，域名含 `at-our.com`，不走代理 |

### 环境变量清单

```dotenv
# =====================
# 数据库
# =====================
DATABASE_URL=postgresql://opsng_user:changeme@postgres:5432/opsng

# =====================
# Redis
# =====================
REDIS_URL=redis://redis:6379

# =====================
# ORY Hydra
# =====================
HYDRA_ADMIN_URL=http://hydra:4445
HYDRA_PUBLIC_URL=http://hydra:4444
HYDRA_SYSTEM_SECRET=change_me_to_a_random_32_char_string

# =====================
# Strapi
# =====================
STRAPI_URL=http://strapi:1337
STRAPI_API_TOKEN=your_strapi_api_token_here

# =====================
# Login App
# =====================
LOGIN_APP_URL=http://login-app:3000

# =====================
# 外部服务（企业内部，不走代理）
# =====================
OPS_SERVICE_URL=http://opsservice.at-our.com
CHAIN_CENTER_URL=http://chaincenter.at-our.com

# =====================
# 代理配置
# =====================
# 容器内访问公网（如拉取 LLM API、pip 镜像等）走代理
HTTP_PROXY=http://127.0.0.1:7890
HTTPS_PROXY=http://127.0.0.1:7890
# 企业内部域名不走代理，直连
NO_PROXY=localhost,127.0.0.1,yaduo.com,at-our.com,postgres,redis,hydra,strapi,login-app,bbf,agent
```

### 数据持久化配置

**PostgreSQL**

- Named Volume：`postgres_data`
- 容器内挂载路径：`/var/lib/postgresql/data`
- 备份建议：定期执行 `pg_dump` 导出，存至宿主机或对象存储

**Redis**

- Named Volume：`redis_data`
- 容器内挂载路径：`/data`
- 配置要求：需启用 AOF 持久化（`--appendonly yes`），防止重启后队列数据丢失

### 代理配置说明

容器内访问公网资源（例如调用 OpenAI API、下载 pip 依赖、拉取模型）时，需通过宿主机代理转发。宿主机代理地址为 `127.0.0.1:7890`，在 Docker Compose 中以环境变量形式注入每个服务。

**企业内部域名必须配置 NO_PROXY。** `yaduo.com` 和 `at-our.com` 为企业内网域名，通过代理访问会导致连接失败。务必将这两个域名加入 `NO_PROXY` 变量，确保流量直连不走代理。

```yaml
# docker-compose.yml 各服务 environment 示例
environment:
  HTTP_PROXY: http://127.0.0.1:7890
  HTTPS_PROXY: http://127.0.0.1:7890
  NO_PROXY: localhost,127.0.0.1,yaduo.com,at-our.com,postgres,redis,hydra,strapi,login-app,bbf,agent
```

注意：`127.0.0.1:7890` 指的是宿主机的代理端口。在 Linux 宿主机的 Docker 容器内，访问宿主机需使用 `host-gateway` 或实际宿主机 IP（如 `172.17.0.1`），需根据实际环境调整。

---

## 与其他模块的关系

| 模块 | 关系说明 |
|------|---------|
| `01-auth.md` | ORY Hydra + Login App 的 OAuth2 流程由本文档配置的容器承载 |
| `02-bbf.md` | FastAPI BBF 的路由和鉴权逻辑运行于本文档定义的 `bbf` 容器中 |
| `03-strapi.md` | Strapi 5 的数据模型和 API 运行于 `strapi` 容器，依赖 `postgres` 容器 |
| `04-agent.md` | Agent Worker 的任务队列依赖 `redis` 容器，任务结果回写依赖 `strapi` 容器 |

---

## 与 Legacy 系统的主要差异

| 维度 | Legacy 系统 | ops-ng 新系统 |
|------|------------|--------------|
| 操作系统 | Windows Server | Linux 容器（Alpine / Debian） |
| 运行时 | IIS + .NET Framework | Docker Compose，各服务独立容器 |
| 数据库 | SQL Server | PostgreSQL 16（统一数据库） |
| 部署方式 | 手动部署，多步骤配置 | `docker compose up -d` 一键启动 |
| 环境依赖 | 依赖 Windows 注册表、GAC、COM 组件 | 无 Windows 依赖，跨平台兼容 |
| 扩展方式 | 垂直扩展（加机器配置） | 水平扩展（增加容器副本） |
| 回滚方式 | 手动替换 dll 文件 | 修改镜像版本号重新 compose up |
