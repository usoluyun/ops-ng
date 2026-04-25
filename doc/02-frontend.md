# 前端 UI

> 文档版本：v0.1 | 最后更新：2026-04-25 | 负责 Agent：Spider-Man

## 概述

ops-ng 前端基于 Next.js 15 App Router 构建，使用 shadcn/ui 组件库和 Tailwind CSS 进行样式开发，TypeScript 保证类型安全。前端承担运维工具的核心操作界面，包括酒店管理和房间管理两大功能模块。

认证采用 ORY Hydra OAuth2/OIDC 标准授权码流程（带 PKCE），登录页由独立部署的 Login App 提供。所有 API 请求统一经过 FastAPI BBF 网关，携带 Bearer token 鉴权。

---

## 功能说明

> 本节面向运维团队

### 功能列表

| 页面 | 路径 | 功能 |
|------|------|------|
| 酒店列表 | `/hotels` | 展示所有酒店，支持按酒店名称搜索过滤 |
| 新建酒店 | `/hotels/new` | 选择酒店、填写地址/电话/传真/区域/城市等信息，上传房间 Excel 文件批量导入房间数据 |
| 编辑酒店 | `/hotels/[id]` | 修改酒店地址、电话、传真、区域、城市、产品类型等信息（ChainID、ChainName、DBName 不可修改），可选择重新上传房间 Excel |
| 酒店上线操作 | `/hotels/[id]/operate` | 执行酒店上线三步流程：配置 Apollo → 初始化数据 → 正式上线，每步操作后显示结果 |
| 房间列表 | `/hotels/[id]/rooms` | 查看指定酒店内所有房间的房号、楼层、房型信息，支持单间删除和房型修改 |
| 新增房间 | `/hotels/[id]/rooms/add` | 批量新增房间，填写房间号（支持自定义分隔符分隔多个房间号）、楼层、房型 |
| 修改房型 | `/hotels/[id]/rooms/modify-type` | 批量修改指定房间的房型，输入房间号列表和目标房型即可 |

### 操作流程

**新建酒店流程：**

1. 进入新建酒店页，从下拉列表中选择目标酒店（从 OpsService 获取未上线酒店列表）
2. 填写酒店地址、电话、传真、邮政编码、区域、城市、产品类型、是否直营、描述等信息
3. 上传包含房间数据的 Excel 文件（格式：楼层、房间号、房型编码），文件须为 .xls 或 .xlsx 格式
4. 提交后系统验证并导入数据，成功后返回酒店列表

**酒店上线流程：**

1. 在酒店列表找到目标酒店，点击"操作"进入上线操作页
2. 第一步：点击"配置 Apollo"，等待后台完成 Apollo 配置
3. 第二步：点击"初始化数据"，等待后台完成数据初始化（包括房间数据、营业日、默认销售员等）
4. 第三步：选择开业日期，点击"正式上线"完成上线

**房间批量操作流程：**

1. 进入房间管理页，查看当前房间列表
2. 新增房间：点击"新增"，填写房间号（多个房间号用指定分隔符分隔）、楼层、房型，提交
3. 批量修改房型：进入修改房型页，输入房间号列表和目标房型，提交

### 注意事项

- ChainID、ChainName、DBName 一旦创建不可修改，编辑酒店时这三个字段仅展示，不可编辑
- 上传 Excel 时，楼层须为正整数，房间号须为 4 位数字，房型编码须在系统中已存在，否则导入失败
- 酒店上线三个步骤须按顺序执行，每步操作为异步任务，需等待后台返回结果再执行下一步
- 房间号为 4 位数字编码，批量操作时注意分隔符格式

---

## 技术设计

> 本节面向开发团队

### 组件职责

| 组件/模块 | 类型 | 职责 |
|-----------|------|------|
| `app/hotels/page.tsx` | Server Component | 酒店列表页，SSR 获取初始数据，渲染酒店表格 |
| `app/hotels/new/page.tsx` | Server Component (外层) | 新建酒店页外层，获取酒店选项和区域列表 |
| `components/hotels/NewHotelForm` | Client Component | 新建酒店表单，处理表单状态、文件上传、提交 |
| `app/hotels/[id]/page.tsx` | Server Component | 编辑酒店页，获取酒店详情 |
| `components/hotels/EditHotelForm` | Client Component | 编辑酒店表单，受控输入，提交修改 |
| `app/hotels/[id]/operate/page.tsx` | Server Component | 上线操作页，获取酒店基本信息 |
| `components/hotels/OperateHotel` | Client Component | 上线三步操作，按步骤调用 API，展示状态 |
| `app/hotels/[id]/rooms/page.tsx` | Server Component | 房间列表页，获取房间数据 |
| `components/rooms/RoomTable` | Client Component | 房间表格，支持删除和行内修改房型 |
| `app/hotels/[id]/rooms/add/page.tsx` | Server Component | 新增房间页外层 |
| `components/rooms/AddRoomForm` | Client Component | 新增房间表单，批量输入 |
| `app/hotels/[id]/rooms/modify-type/page.tsx` | Server Component | 修改房型页外层 |
| `components/rooms/ModifyRoomTypeForm` | Client Component | 批量修改房型表单 |
| `lib/api-client.ts` | 工具模块 | 封装 fetch，自动附加 Bearer token，统一错误处理 |
| `lib/auth.ts` | 工具模块 | OAuth2 token 管理，refresh 逻辑 |

### 关键接口 / API

所有接口均通过 BBF 网关代理，前端请求路径以 `/api` 为前缀。

| 接口 | 方法 | 说明 |
|------|------|------|
| `GET /api/hotels` | GET | 获取酒店列表，支持 `?name=` 过滤 |
| `GET /api/hotels/unregistered` | GET | 获取未上线酒店列表（新建时使用） |
| `POST /api/hotels` | POST | 新建酒店（multipart/form-data，含 Excel 文件） |
| `GET /api/hotels/{id}` | GET | 获取单个酒店详情 |
| `PUT /api/hotels/{id}` | PUT | 修改酒店信息（可选附带 Excel 文件） |
| `POST /api/hotels/{id}/configure-apollo` | POST | 第一步：配置 Apollo |
| `POST /api/hotels/{id}/init-data` | POST | 第二步：初始化数据 |
| `POST /api/hotels/{id}/go-online` | POST | 第三步：正式上线 |
| `GET /api/hotels/{id}/rooms` | GET | 获取酒店房间列表 |
| `POST /api/hotels/{id}/rooms` | POST | 批量新增房间 |
| `PUT /api/hotels/{id}/rooms/room-type` | PUT | 批量修改房型 |
| `DELETE /api/hotels/{id}/rooms` | DELETE | 批量删除房间（`?roomNos=` 参数） |
| `GET /api/areas` | GET | 获取区域列表 |
| `GET /api/cities/{id}` | GET | 获取城市信息 |
| `GET /api/room-types?chainId={id}` | GET | 获取指定酒店可用房型列表 |

### 数据流

#### 路由设计（Next.js App Router）

| 路由 | 说明 |
|------|------|
| `/` | 重定向到 `/hotels` |
| `/hotels` | 酒店列表 |
| `/hotels/new` | 新建酒店 |
| `/hotels/[id]` | 酒店详情/编辑 |
| `/hotels/[id]/operate` | 酒店上线操作 |
| `/hotels/[id]/rooms` | 房间管理 |
| `/hotels/[id]/rooms/add` | 新增房间 |
| `/hotels/[id]/rooms/modify-type` | 批量修改房型 |
| `/login` | 登录页（由 Login App 独立部署提供，Next.js 重定向） |
| `/auth/callback` | OAuth2 回调处理，接收 code，换取 token |

#### 认证集成

**OAuth2 授权码流程（带 PKCE）：**

1. 用户访问受保护页面，前端检测无有效 token，发起 OAuth2 redirect
2. 前端生成 `code_verifier` 和 `code_challenge`（PKCE），重定向至 Hydra `/oauth2/auth`
3. Hydra 重定向到 Login App 登录页，用户输入凭证
4. Login App 验证通过后，Hydra 携带 `code` 回调前端 `/auth/callback`
5. 前端用 `code` + `code_verifier` 向 Hydra `/oauth2/token` 换取 `access_token` 和 `refresh_token`
6. `access_token` 存储于 **httpOnly cookie**（由 Next.js Route Handler 设置），不暴露给 JavaScript
7. `refresh_token` 同样存于 httpOnly cookie

**Token 存储策略：**

- `access_token`：httpOnly cookie，不可被 JS 访问，防止 XSS
- 不使用 localStorage 或 sessionStorage 存储 token

**请求拦截器：**

- 客户端请求通过 `lib/api-client.ts` 统一发出
- Next.js Server Components 和 Route Handlers 从 cookie 读取 token，附加 `Authorization: Bearer <token>` header 再转发给 BBF

**401 响应处理：**

- `api-client.ts` 捕获 401 响应，自动尝试用 `refresh_token` 刷新 `access_token`
- 刷新成功：更新 cookie 中的 token，重试原请求
- 刷新失败（token 过期或撤销）：清除 cookie，重定向到登录页

#### 页面跳转关系图

```mermaid
flowchart TD
    A[用户访问] --> B{已登录?}
    B -- 否 --> C[重定向 Hydra OAuth2]
    C --> D[Login App 登录页]
    D --> E[Hydra 回调 /auth/callback]
    E --> F[换取 token 写入 cookie]
    F --> G[/hotels 酒店列表]
    B -- 是 --> G

    G --> H[/hotels/new 新建酒店]
    G --> I[/hotels/id 编辑酒店]
    G --> J[/hotels/id/operate 上线操作]
    G --> K[/hotels/id/rooms 房间列表]

    J --> J1[第一步: 配置 Apollo]
    J1 --> J2[第二步: 初始化数据]
    J2 --> J3[第三步: 正式上线]
    J3 --> G

    K --> L[/hotels/id/rooms/add 新增房间]
    K --> M[/hotels/id/rooms/modify-type 修改房型]
    L --> K
    M --> K
    H --> G
    I --> G
```

#### Excel 上传数据流

```
前端 (multipart/form-data)
  → Next.js Route Handler (/api/hotels POST)
    → BBF (转发 multipart, Bearer token)
      → Agent 服务 (解析 Excel, 验证房间数据)
        → Strapi (持久化酒店和房间数据)
```

#### 状态管理策略

- **初始数据加载**：Server Components 通过 Next.js 服务端直接调用 BBF，数据随 HTML 下发
- **客户端交互数据**：使用 SWR 或 TanStack Query 管理，支持 mutation 和乐观更新
- **表单状态**：React Hook Form + Zod schema 校验
- **上线操作进度**：Client Component 本地 useState 管理步骤状态，每步 await API 响应后推进

### 依赖的外部服务

| 服务 | 用途 | 调用方式 |
|------|------|----------|
| ORY Hydra | OAuth2 授权，颁发 access_token / refresh_token | 前端 redirect，/auth/callback 换 token |
| Login App | 提供登录 UI 和 Consent 处理 | Hydra 回调触发，独立部署 |
| FastAPI BBF | 所有业务 API 的统一入口 | HTTP + Bearer token |
| OpsService（经 BBF） | 酒店列表、区域、城市、房间数据 CRUD | 通过 BBF 代理 |
| ChainCenter（经 BBF） | 房型数据查询 | 通过 BBF 代理 |
| Agent 服务（经 BBF） | Excel 解析、酒店上线异步任务 | 通过 BBF 投递任务队列 |

---

## 与其他模块的关系

- **BBF（FastAPI）**：前端所有业务请求的唯一入口，BBF 负责 token 验证、路由转发和服务编排，前端无需直接感知 Strapi 或 Agent 的存在
- **Login App**：负责登录页面渲染和用户凭证验证，前端通过 OAuth2 redirect 与之交互，不直接调用其接口
- **ORY Hydra**：前端仅在认证流程中与 Hydra 标准端点交互（`/oauth2/auth`、`/oauth2/token`），业务请求不经过 Hydra
- **Agent 服务**：前端通过 BBF 触发异步任务（如酒店上线三步操作、Excel 导入），不直接与 Agent 通信，任务状态通过轮询 BBF 接口获取

---

## 与 Legacy 系统的主要差异

| 维度 | Legacy 系统 | ops-ng 新系统 |
|------|-------------|---------------|
| 框架 | .NET MVC，Razor 服务端渲染 | Next.js 15 App Router，React Server Components |
| 前端技术 | jQuery + Bootstrap，页面全量刷新 | React + shadcn/ui + Tailwind CSS，局部更新 |
| 语言 | C# | TypeScript |
| 认证 | 自研 `[Login]` Filter，Session 校验 | ORY Hydra OAuth2/OIDC，标准授权码流程 + PKCE |
| Token 存储 | 服务端 Session | httpOnly cookie（access_token + refresh_token） |
| API 通信 | Controller 直接调用 OpsService HTTP 接口 | 前端 → BBF → Strapi/Agent，统一经过 BBF 鉴权网关 |
| 数据获取 | 服务端同步调用，ViewBag 传递数据 | Server Components SSR + SWR 客户端缓存 |
| 表单验证 | 服务端 `CheckMessage()` 方法 | 前端 Zod schema + React Hook Form，服务端 BBF 二次校验 |
| Excel 解析 | .NET 服务端 OleDB 直接读取 | 前端上传 multipart → BBF → Agent 服务解析 |
| 路由 | `/Home/Index`、`/Home/EditChain` 等 MVC 路由 | `/hotels`、`/hotels/[id]` 等 RESTful 路径 |
| 部署 | 单体 IIS 部署 | Docker Compose / K8s 微服务部署 |
