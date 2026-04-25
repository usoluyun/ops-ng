# 迁移规划：Legacy ASP.NET MVC → Next.js + FastAPI

## Context

将亚朵运维工具系统 (ASP.NET MVC 5 + Razor + SQL Server) 迁移到现代架构：
- **前端**: Next.js (App Router) + shadcn/ui + Tailwind CSS
- **后端**: Python FastAPI
- **数据库**: 先保留 SQL Server，逐步迁移到 serverless OSS
- **范围**: 核心模块 (酒店管理、房间管理、房单管理)
- **部署**: 本地 + chester.monster

---

## 项目结构

```
ops-ng/
├── frontend/          # Next.js
│   └── src/
│       ├── app/        # App Router pages
│       │   ├── (auth)/login/
│       │   ├── (dashboard)/chain/
│       │   ├── (dashboard)/room/
│       │   ├── (dashboard)/folio/
│       │   └── api/    # API routes
│       ├── components/ui/     # shadcn/ui
│       ├── components/chain/  # 业务组件
│       ├── components/room/
│       ├── components/folio/
│       ├── lib/api/   # API client
│       ├── types/     # TypeScript types
│       └── hooks/
├── backend/           # FastAPI
│   ├── app/
│   │   ├── api/v1/    # 路由
│   │   ├── core/      # 配置、数据库、安全
│   │   ├── db/        # ORM 模型
│   │   ├── schemas/   # Pydantic models
│   │   └── services/  # 业务逻辑 + 外部服务
│   └── requirements.txt
└── CLAUDE.md
```

---

## 认证与权限设计

### 认证流程：邮箱验证码登录

```
用户输入企业邮箱 → 系统验证邮箱域名(@yaduo.com/@at-our.com) →
发送6位验证码到邮箱 → 用户输入验证码 → 登录成功
```

**API 设计:**

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/v1/auth/send-code` | 发送验证码到邮箱 |
| POST | `/api/v1/auth/verify-code` | 验证验证码并登录 |
| POST | `/api/v1/auth/logout` | 登出 |
| GET | `/api/v1/auth/me` | 获取当前用户信息 |

**验证码规则:**
- 6位数字
- 有效期15分钟
- 同一邮箱5分钟内不能重复发送
- 错误5次后需等待30分钟

### 权限控制：模块级 + 关键操作控制

权限基于角色，分模块权限和关键操作权限：

| 角色 | 可访问模块 | 可执行关键操作 |
|------|-----------|---------------|
| admin | 全部模块 | 全部关键操作 |
| hotel_manager | 酒店管理、房间管理 | - |
| online_operator | 房单管理、账务操作 | **酒店上下线、房间上下线** |
| folio_operator | 房单管理、账务操作 | - |

**关键操作权限 (需要特定角色):**

| 操作 | 需要的角色 |
|------|-----------|
| 酒店上线 OnLine | online_operator |
| 酒店下线 OffLine | online_operator |
| 房间上线 | online_operator |
| 房间下线 | online_operator |

**实现方式:**
```python
from enum import Enum

class Role(str, Enum):
    ADMIN = "admin"
    HOTEL_MANAGER = "hotel_manager"
    ONLINE_OPERATOR = "online_operator"
    FOLIO_OPERATOR = "folio_operator"

class Module(str, Enum):
    CHAIN = "chain"       # 酒店管理
    ROOM = "room"         # 房间管理
    FOLIO = "folio"       # 房单管理

class Action(str, Enum):
    CHAIN_ONLINE = "chain_online"
    CHAIN_OFFLINE = "chain_offline"
    ROOM_ONLINE = "room_online"
    ROOM_OFFLINE = "room_offline"

ROLE_PERMISSIONS = {
    Role.ADMIN: {"modules": [Module.CHAIN, Module.ROOM, Module.FOLIO], "actions": "*"},
    Role.HOTEL_MANAGER: {"modules": [Module.CHAIN, Module.ROOM], "actions": []},
    Role.ONLINE_OPERATOR: {"modules": [Module.CHAIN, Module.ROOM, Module.FOLIO], "actions": [Action.CHAIN_ONLINE, Action.CHAIN_OFFLINE, Action.ROOM_ONLINE, Action.ROOM_OFFLINE]},
    Role.FOLIO_OPERATOR: {"modules": [Module.FOLIO], "actions": []},
}
```

**API 权限检查示例:**
```python
# 酒店上线需要 online_operator 角色
@router.post("/chains/{chain_id}/online")
async def chain_online(chain_id: int, current_user: User = Depends(get_current_user)):
    require_action(current_user, Action.CHAIN_ONLINE)
    # 执行上线逻辑
```

---

## 核心 API 设计

### 认证 `/api/v1/auth`
| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/auth/send-code` | 发送验证码到邮箱 |
| POST | `/auth/verify-code` | 验证码登录 |
| POST | `/auth/logout` | 登出 |
| GET | `/auth/me` | 获取当前用户 |

### 酒店管理 `/api/v1/chains`
| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/chains` | 获取酒店列表 |
| GET | `/chains/{id}` | 获取单个酒店 |
| POST | `/chains` | 创建酒店 |
| PUT | `/chains/{id}` | 更新酒店 |

### 房间管理 `/api/v1/chains/{chain_id}/rooms`
| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/rooms` | 获取房间列表 |
| POST | `/rooms` | 批量添加房间 |
| PUT | `/rooms` | 批量修改房型 |
| DELETE | `/rooms` | 批量删除房间 |

### 房单管理 `/api/v1/chains/{chain_id}/folios`
| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/folios` | 获取房单列表 (分页) |
| GET | `/folios/{id}` | 获取房单详情 |
| GET | `/folios/{id}/transactions` | 获取账务 |
| GET | `/folios/{id}/guests` | 获取客人信息 |
| POST | `/folios/{id}/transactions` | 添加账务 |
| POST | `/folios/{id}/deduct` | 批量冲减 |
| POST | `/folios/{id}/transfer` | 转账 |

---

## 关键技术决策

### 1. 多数据库路由
```python
# DatabaseRouter 根据 ChainID 动态路由到对应的 FO 数据库
# 支持 AutoDB/FO/EB/BI/CC 等多数据源
# 缓存 Chain -> DBName 映射
```

### 2. 外部服务封装
- **OpsService**: HTTP REST 调用 (httpx)
- **CenterService**: SOAP 调用 (zeep)
- **SecurityService**: 加密/解密手机号、证件号

### 3. 数据加密处理
手机号、证件号通过 SecurityService 加密存储，API 返回时解密

---

## 分阶段实施计划

### 第一阶段：基础架构 (4-6 周)

**后端:**
- Week 1-2: FastAPI 项目初始化、SQLAlchemy 配置、DatabaseRouter
- Week 3-4: 外部服务客户端 (Ops, Center, Security, ChainCenter)
- Week 5-6: 酒店管理 CRUD API、JWT 认证

**前端:**
- Week 1-2: Next.js 初始化、shadcn/ui 配置、布局组件
- Week 3-4: API 客户端封装、TypeScript 类型定义、Zustand 状态管理
- Week 5-6: 登录页面、路由守卫

### 第二阶段：核心业务 (6-8 周)

**房间管理 (3-4 周):**
- 房间列表页面 (搜索/过滤)
- 批量添加/修改/删除房间
- 与 Ops 服务集成

**房单管理 (4-5 周):**
- 房单列表 (多条件搜索)
- 房单详情 (客人信息解密显示)
- 账务操作 (添加/冲减/转账)

**房型管理 (1 周):**
- 房型列表
- ChainCenter 同步

### 第三阶段：完善优化 (4-6 周)
- 报表、数据导出
- 性能优化
- 部署到 chester.monster

---

## 关键参考文件

| 原文件 | 用途 |
|--------|------|
| `legacy/.../BLL/AppContext.cs` | 全局服务上下文、多数据库访问模式 |
| `legacy/.../DAL/FoFolioDAL.cs` | 分页查询、加密字段处理 |
| `legacy/.../Controllers/RoomController.cs` | 外部服务集成模式 |
| `legacy/.../Security/SecurityUtil.cs` | 加密/解密逻辑 |
| `legacy/.../Models/FoFolio.cs` | 核心数据模型 |

---

## 验证计划

1. **本地开发环境验证:**
   - 启动 FastAPI: `uvicorn app.main:app --reload`
   - 启动 Next.js: `npm run dev`
   - 测试酒店 CRUD API
   - 测试房间管理功能

2. **远程部署验证:**
   - 推送代码到 git
   - 在 chester.monster 部署
   - 验证完整业务流程

3. **回归测试:**
   - 对比新旧系统数据一致性
   - 验证外部服务调用结果