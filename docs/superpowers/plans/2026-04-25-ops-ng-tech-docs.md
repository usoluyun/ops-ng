# ops-ng 技术文档撰写实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 ops-ng 系统撰写 10 篇结构一致的技术文档，覆盖酒店与房型维护功能的所有架构层级。

**Architecture:** 每篇文档分两部分：功能说明（运维人员读）+ 技术设计（开发人员读），使用统一模板，包含 Mermaid 图表和接口规范。

**Tech Stack:** Markdown + Mermaid，输出到 `/Users/luyun/Documents/poc/ops-ng/doc/` 目录。

---

## 关键信息源

所有 agent 在撰写前必须读取：

- 架构文档：`/Users/luyun/Documents/poc/ops-ng/doc/architecture-v2.md`
- 设计规范：`/Users/luyun/Documents/poc/ops-ng/docs/superpowers/specs/2026-04-25-tech-doc-design.md`
- Legacy 控制器：`/Users/luyun/Documents/poc/ops-ng/legacy/operationtool/AutoDBSystem/Controllers/HomeController.cs`
- Legacy 控制器：`/Users/luyun/Documents/poc/ops-ng/legacy/operationtool/AutoDBSystem/Controllers/RoomController.cs`
- Legacy DAL：`/Users/luyun/Documents/poc/ops-ng/legacy/operationtool/AutoDBSystem/DAL/ChainDAL.cs`

---

## 文档统一模板

每篇文档必须严格遵循以下结构：

```markdown
# [模块名称]

> 文档版本：v0.1 | 最后更新：YYYY-MM-DD | 负责 Agent：[漫威代号]

## 概述

[2-3 句话：这个模块是什么、解决什么问题、谁在用它]

## 功能说明

> 本节面向运维团队

### 功能列表

| 功能 | 说明 |
|------|------|
| ... | ... |

### 操作流程

[步骤说明，无需代码，用编号列表]

### 注意事项

[限制、常见问题、必须知道的约束]

## 技术设计

> 本节面向开发团队

### 组件职责

[职责边界说明]

### 关键接口 / API

[接口签名、请求/响应示例]

### 数据流

[Mermaid 时序图或流程图]

### 依赖的外部服务

[上下游依赖说明]

## 与其他模块的关系

[上下游依赖、调用关系]

## 与 Legacy 系统的主要差异

[新系统在这个模块上相对 legacy 的变化]
```

---

## 验证检查清单（每篇文档完成后执行）

- [ ] 文档包含全部 6 个章节（概述、功能说明、技术设计、模块关系、Legacy 差异）
- [ ] 功能说明章节无代码，使用表格/列表
- [ ] 技术设计章节包含至少一个 Mermaid 图
- [ ] 技术设计章节包含至少一个接口示例（如适用）
- [ ] 文档头部包含版本号和 agent 代号
- [ ] 文件保存在 `/Users/luyun/Documents/poc/ops-ng/doc/` 目录

---

## Task 1: Nick Fury — 00-overview.md 系统总览

**Taskwarrior ID:** 40
**Files:** Create `doc/00-overview.md`

- [ ] 读取架构文档 `doc/architecture-v2.md`
- [ ] 撰写**概述**：ops-ng 是什么，取代什么，服务于哪个团队
- [ ] 撰写**功能说明**：列出系统提供的主要功能模块（酒店管理、房间管理、认证），附操作入口说明
- [ ] 撰写**技术设计**：复制并说明架构图（整体架构 Mermaid 图），解释各层职责和数据流向
- [ ] 撰写**技术栈表格**：对照 `architecture-v2.md` 中技术栈章节，每行加一句"为什么选这个"的说明
- [ ] 撰写**模块索引**：列出 01-09 文档链接和一句话说明
- [ ] 运行验证检查清单
- [ ] `git add doc/00-overview.md && git commit -m "docs: add 00-overview.md (Nick Fury)"`
- [ ] `task 40 done`
- [ ] `jrnl "Nick Fury 完成 00-overview.md @ops-ng @doc"`

---

## Task 2: Black Widow — 01-auth.md 认证模块

**Taskwarrior ID:** 41
**Files:** Create `doc/01-auth.md`

- [ ] 读取架构文档中 ORY Hydra 和 Login App 章节
- [ ] 撰写**概述**：认证层的职责，用户如何登录，token 如何颁发
- [ ] 撰写**功能说明**：登录流程步骤（用户点击登录 → Hydra 授权 → Login App 验证 → 返回 Token）；登出；Token 刷新
- [ ] 撰写**技术设计**：
  - ORY Hydra endpoints 列表（`/oauth2/auth`, `/oauth2/token`, `/oauth2/userinfo`, `/oauth2/revoke`）
  - Login App 职责：渲染登录表单、调用 Strapi 验证用户、回调 Hydra Consent
  - OAuth2 授权码流程完整时序图（Mermaid sequenceDiagram，9 步流程来自架构文档）
  - 标注未定技术决策：Login App 用 FastAPI 还是 Next.js（风险 task #50）
- [ ] 撰写 **Legacy 差异**：legacy 用手机号+短信验证码登录，新系统升级为标准 OAuth2/OIDC
- [ ] 运行验证检查清单
- [ ] `git add doc/01-auth.md && git commit -m "docs: add 01-auth.md (Black Widow)"`
- [ ] `task 41 done`
- [ ] `jrnl "Black Widow 完成 01-auth.md @ops-ng @doc"`

---

## Task 3: Spider-Man — 02-frontend.md 前端 UI

**Taskwarrior ID:** 42
**Files:** Create `doc/02-frontend.md`

- [ ] 读取架构文档 Next.js UI 章节和 legacy 系统页面功能（HomeController + RoomController）
- [ ] 撰写**概述**：Next.js UI 是运维团队使用的 Web 界面，shadcn/ui 组件库
- [ ] 撰写**功能说明**：
  - 页面列表：酒店列表页、酒店详情/编辑页、房间管理页、登录页
  - 每个页面的操作步骤说明（无代码）
- [ ] 撰写**技术设计**：
  - 路由设计（Next.js App Router 建议路由结构：`/hotels`, `/hotels/[id]`, `/hotels/[id]/rooms`）
  - 认证集成：如何处理 OAuth2 redirect，存储 token，刷新 token
  - 与 BBF 的 HTTP 通信（请求鉴权方式：Bearer token header）
  - 状态管理策略建议（Server Components + SWR/React Query for client data）
  - Mermaid 流程图：页面跳转关系
- [ ] 撰写 **Legacy 差异**：legacy 是 .NET MVC 服务端渲染，新系统是 Next.js SPA/SSR
- [ ] 运行验证检查清单
- [ ] `git add doc/02-frontend.md && git commit -m "docs: add 02-frontend.md (Spider-Man)"`
- [ ] `task 42 done`
- [ ] `jrnl "Spider-Man 完成 02-frontend.md @ops-ng @doc"`

---

## Task 4: Iron Man — 03-bbf-gateway.md BBF 网关

**Taskwarrior ID:** 43
**Files:** Create `doc/03-bbf-gateway.md`

- [ ] 读取架构文档 FastAPI BBF 章节
- [ ] 撰写**概述**：BBF 是所有客户端请求的唯一入口，负责鉴权、路由、编排
- [ ] 撰写**功能说明**：
  - 鉴权拦截：所有请求必须带有效 Bearer token
  - 路由规则：哪些路径转发到 Strapi，哪些触发 Agent 任务
  - 限流说明（频次上限，超限返回 429）
- [ ] 撰写**技术设计**：
  - Token 验证流程（JWT 验证 vs 调用 Hydra introspect）
  - 路由配置表（`GET /api/hotels` → Strapi，`POST /api/hotels/{id}/online` → Redis Queue）
  - 服务编排示例：酒店上线需依次调用多个下游服务时的编排逻辑
  - Mermaid 流程图：请求进入 BBF 到响应返回的完整流程
  - 错误响应规范（4xx/5xx 统一格式）
- [ ] 撰写 **Legacy 差异**：legacy 无独立网关层，直接在 .NET Controller 内调用 OpsService
- [ ] 运行验证检查清单
- [ ] `git add doc/03-bbf-gateway.md && git commit -m "docs: add 03-bbf-gateway.md (Iron Man)"`
- [ ] `task 43 done`
- [ ] `jrnl "Iron Man 完成 03-bbf-gateway.md @ops-ng @doc"`

---

## Task 5: Thor — 04-strapi-data.md 主数据服务

**Taskwarrior ID:** 44
**Files:** Create `doc/04-strapi-data.md`

- [ ] 读取架构文档 Strapi 5 章节 + legacy ChainDAL.cs 中的 Chain 数据结构
- [ ] 撰写**概述**：Strapi 5 管理所有业务主数据和用户账号，提供自动生成的 REST/GraphQL API
- [ ] 撰写**功能说明**：
  - 酒店数据维护（新增、编辑、查询）
  - 房型数据维护（查询、同步）
  - 用户管理（Login App 调用此处验证用户凭证）
- [ ] 撰写**技术设计**：
  - Content Types 定义：Hotel（对照 legacy Chain 模型字段：ChainID, ChainName, ChainAddress, Telephone, Fax, CityID, AreaID, PostCode, Product, IsGuide, Status, OpenDate）、Room、RoomType、User
  - 关键 API 端点（`GET /api/hotels`, `POST /api/hotels`, `PUT /api/hotels/:id`）
  - 权限控制：哪些接口需要认证，哪些公开
  - 与 PostgreSQL 的关系（Strapi ORM 统一管理，不直接写 SQL）
  - Mermaid 图：Strapi ↔ PostgreSQL ↔ 其他服务的关系
- [ ] 撰写 **Legacy 差异**：legacy 直接 SQL 操作多个数据库（AutoDB/CC/FO/BI），新系统通过 Strapi API 统一访问单一 PostgreSQL
- [ ] 运行验证检查清单
- [ ] `git add doc/04-strapi-data.md && git commit -m "docs: add 04-strapi-data.md (Thor)"`
- [ ] `task 44 done`
- [ ] `jrnl "Thor 完成 04-strapi-data.md @ops-ng @doc"`

---

## Task 6: Doctor Strange — 05-agent-service.md Agent 服务

**Taskwarrior ID:** 45
**Files:** Create `doc/05-agent-service.md`

- [ ] 读取架构文档 Agent 服务章节（LangChain + LangGraph + Dramatiq）
- [ ] 撰写**概述**：Agent 服务是后台批量任务执行引擎，处理需要调用多个外部服务的复杂流程
- [ ] 撰写**功能说明**：
  - 酒店上线流程任务（对照 legacy：配置 Apollo → 初始化数据 → 正式上线）
  - 房型同步任务（从 ChainCenter 同步房型到分库）
  - 任务状态查询（运维人员可查看任务执行进度）
- [ ] 撰写**技术设计**：
  - 任务队列流程（BBF → Dramatiq Task → Redis Queue → Agent Worker → LangGraph → 结果回写 Strapi）
  - Mermaid 时序图：完整异步任务生命周期
  - LangGraph 工作流节点说明（以酒店上线为例：node1=验证参数, node2=调用OpsService, node3=初始化数据, node4=上线, node5=回写结果）
  - 外部服务调用（OpsService, CenterService SOAP, ChainCenter）— 注明接口详情未文档化（风险 task #54）
  - 任务幂等性和失败重试策略
- [ ] 撰写 **Legacy 差异**：legacy 在 HTTP 请求中同步调用 OpsService，新系统异步队列解耦，支持重试和状态追踪
- [ ] 运行验证检查清单
- [ ] `git add doc/05-agent-service.md && git commit -m "docs: add 05-agent-service.md (Doctor Strange)"`
- [ ] `task 45 done`
- [ ] `jrnl "Doctor Strange 完成 05-agent-service.md @ops-ng @doc"`

---

## Task 7: Captain America — 06-hotel-management.md 酒店管理

**Taskwarrior ID:** 46
**Files:** Create `doc/06-hotel-management.md`

- [ ] 读取 legacy `HomeController.cs` 中的所有酒店相关方法
- [ ] 撰写**概述**：酒店管理是系统的核心业务，管理亚朵集团所有门店的主数据和生命周期
- [ ] 撰写**功能说明**：
  - 酒店列表与搜索（按名称搜索）
  - 新建酒店（选择酒店、填写信息、上传房间 Excel）
  - 编辑酒店信息（不可修改：ChainID、ChainName、DBName）
  - 酒店改名（跨多系统同步）
  - 酒店上线流程（3步：配置 → 初始化数据 → 正式上线）
  - 酒店下线
  - 初始化营业日
- [ ] 撰写**技术设计**：
  - 端到端 API 调用链（UI → BBF → Strapi/Agent → 外部服务）
  - 酒店上线 Mermaid 时序图（对照 legacy 的 ConfigApollo → InitData → OnLine 三步流程）
  - 酒店数据字段映射表（legacy `Chain` 模型 → 新系统 Strapi Content Type）
  - Excel 导入房间数据的处理流程（legacy 用 OleDb 解析 xls，新系统改为标准文件上传 API）
- [ ] 撰写 **Legacy 差异**：legacy 通过 OpsService HTTP 接口操作，同时直写多个 SQL 数据库（CC/FO/BI）；新系统通过 Agent 异步编排，统一写 Strapi
- [ ] 运行验证检查清单
- [ ] `git add doc/06-hotel-management.md && git commit -m "docs: add 06-hotel-management.md (Captain America)"`
- [ ] `task 46 done`
- [ ] `jrnl "Captain America 完成 06-hotel-management.md @ops-ng @doc"`

---

## Task 8: Hawkeye — 07-room-management.md 房间与房型管理

**Taskwarrior ID:** 47
**Files:** Create `doc/07-room-management.md`

- [ ] 读取 legacy `RoomController.cs` 中的所有方法
- [ ] 撰写**概述**：房间管理负责维护酒店内每个物理房间的数据，房型管理负责维护房型分类
- [ ] 撰写**功能说明**：
  - 查看酒店房间列表
  - 新增房间（批量，支持分隔符，需填写：房间号、房型、楼层）
  - 删除房间（单个 / 批量）
  - 修改房间房型（单个 / 批量）
  - 修复房态
  - 查询房型列表（来自 ChainCenter）
  - 同步房型到分库
- [ ] 撰写**技术设计**：
  - 批量操作 API 设计（`PATCH /api/hotels/{id}/rooms` with room_ids array）
  - 房型同步流程 Mermaid 图（BBF → Agent → ChainCenter → Strapi）
  - 房间数据模型（RoomNo, RoomType, Floor, ChainID）
  - 修复房态的含义和触发条件（legacy 调用存储过程 `p_r_RepairRoomStatus`）
- [ ] 撰写 **Legacy 差异**：legacy 批量操作通过逗号分隔字符串传递房间号；新系统使用 JSON array；房型同步从调用 chain-center SOAP 改为通过 Agent 异步处理
- [ ] 运行验证检查清单
- [ ] `git add doc/07-room-management.md && git commit -m "docs: add 07-room-management.md (Hawkeye)"`
- [ ] `task 47 done`
- [ ] `jrnl "Hawkeye 完成 07-room-management.md @ops-ng @doc"`

---

## Task 9: Black Panther — 08-data-model.md 数据模型

**Taskwarrior ID:** 48
**Files:** Create `doc/08-data-model.md`

- [ ] 读取 legacy `ChainDAL.cs` 中所有 SQL 语句和字段，以及 legacy Models 目录下 `Chain.cs`, `FoRoom.cs`, `FoRoomType.cs`
- [ ] 撰写**概述**：所有业务数据统一存储在 PostgreSQL，通过 Strapi ORM 访问，不再分散到多个数据库
- [ ] 撰写**功能说明**：主要数据实体列表，各实体负责存什么数据（运维人员无需关注字段细节，只需知道数据在哪）
- [ ] 撰写**技术设计**：
  - Hotel 表字段定义（对照 legacy `c_chain` 表：ChainID, ChainName, DBName, ChainAddress, Telephone, Fax, CityID, AreaID, PostCode, Remark, Product, IsGuide, Status, Step, OpenDate, Instance）
  - Room 表字段定义（RoomID, ChainID, RoomNo, RoomType, Floor）
  - RoomType 表字段定义（对照 legacy `r_RoomType`：RoomTypeID, RoomTypeName, RoomTypeCode, BedCount, MaxCheckInCount, Remark, MasterRoomTypeID, Flag, Description, Sort）
  - User 表字段定义（由 Strapi 用户管理插件提供）
  - Mermaid ER 图：Hotel ←→ Room ←→ RoomType 关系
  - 索引策略（ChainID 为高频查询字段，需要索引）
- [ ] 撰写 **Legacy 差异**：legacy 数据分散在 AutoDB（c_chain）、FO 分库（r_Room/r_RoomType）、CC 库、BI 库；新系统统一 PostgreSQL 单库
- [ ] 运行验证检查清单
- [ ] `git add doc/08-data-model.md && git commit -m "docs: add 08-data-model.md (Black Panther)"`
- [ ] `task 48 done`
- [ ] `jrnl "Black Panther 完成 08-data-model.md @ops-ng @doc"`

---

## Task 10: War Machine — 09-deployment.md 部署配置

**Taskwarrior ID:** 49
**Files:** Create `doc/09-deployment.md`

- [ ] 读取架构文档部署架构章节（Docker Compose / K8s 章节）
- [ ] 撰写**概述**：系统通过 Docker Compose 本地部署或 Kubernetes 生产部署，所有服务容器化
- [ ] 撰写**功能说明**：
  - 本地开发启动步骤（3步：clone → env 配置 → docker compose up）
  - 服务健康检查地址
  - 常见故障排查（服务起不来、连不上数据库、Redis 队列堵塞）
- [ ] 撰写**技术设计**：
  - 服务清单（Hydra, Login App, BBF, Strapi, Agent Worker, PostgreSQL, Redis）
  - 端口映射表（各服务对外端口）
  - 环境变量清单（必填项：DATABASE_URL, REDIS_URL, HYDRA_URL, STRAPI_URL, OPS_SERVICE_URL, CHAIN_CENTER_URL）
  - Docker Compose 服务依赖关系 Mermaid 图
  - 数据持久化配置（PostgreSQL 和 Redis 的 volume 挂载）
  - 代理配置说明：命令行需设置 `HTTP_PROXY=127.0.0.1:7890`；yaduo.com / at-our.com 内部域名加入 `NO_PROXY`
- [ ] 撰写 **Legacy 差异**：legacy 部署在 IIS + SQL Server，新系统全容器化，无 Windows 依赖
- [ ] 运行验证检查清单
- [ ] `git add doc/09-deployment.md && git commit -m "docs: add 09-deployment.md (War Machine)"`
- [ ] `task 49 done`
- [ ] `jrnl "War Machine 完成 09-deployment.md @ops-ng @doc"`

---

## 全部完成后

- [ ] `task project:ops-ng.docs +doc list` — 确认 10 个 doc 任务全部 done
- [ ] `jrnl "ops-ng 技术文档 10 篇全部完成，待 review @ops-ng @doc @milestone"`
- [ ] 提交汇总 PR 或通知人工 review
