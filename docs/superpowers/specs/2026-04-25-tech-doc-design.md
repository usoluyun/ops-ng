# ops-ng 技术文档撰写设计

**日期**: 2026-04-25
**项目**: ops-ng — 亚朵集团酒店运维管理系统（下一代）
**目标受众**: 负责产品运维的团队（功能部分）+ 开发团队（技术部分）

---

## 背景

ops-ng 是对 legacy .NET 运维工具（AutoDBSystem）的重写，基于新架构（Next.js + FastAPI BBF + Strapi 5 + ORY Hydra + Agent 服务）。

当前阶段覆盖 legacy 系统中的**酒店与房型维护功能**（排除订单、账务相关功能）。

---

## 文档范围

以下功能来自 legacy 系统分析，纳入本次文档：

- 认证登录（手机号 + 短信验证码 → 升级为 OAuth2/OIDC）
- 酒店列表、搜索、新建、编辑、改名
- 酒店上线/下线生命周期（配置 → 初始化 → 上线）
- 房间管理（新增/删除/批量操作/修复房态）
- 房型管理（查询/同步）

---

## 文档目录结构

```
doc/
  00-overview.md           # 系统总览：架构图、模块关系、技术栈
  01-auth.md               # 认证模块：ORY Hydra + Login App
  02-frontend.md           # 前端 UI：Next.js 页面、路由、状态管理
  03-bbf-gateway.md        # BBF 网关：路由、鉴权、限流、编排
  04-strapi-data.md        # 主数据服务：Content Types、API、用户管理
  05-agent-service.md      # Agent 服务：异步任务、LangGraph 工作流
  06-hotel-management.md   # 业务：酒店管理端到端
  07-room-management.md    # 业务：房间与房型管理端到端
  08-data-model.md         # 数据模型：PostgreSQL 表结构与关系
  09-deployment.md         # 部署：Docker Compose、配置、环境变量
```

---

## 每篇文档的统一结构

```markdown
# 模块名称

## 概述
简短说明：这个模块是什么、解决什么问题、谁在用它

## 功能说明（运维读）
- 功能列表
- 操作流程（步骤说明）
- 关键限制与注意事项

## 技术设计（开发读）
- 组件职责与边界
- 关键接口 / API
- 数据流 / 时序图（Mermaid）
- 依赖的外部服务

## 与其他模块的关系
- 上下游依赖说明
```

---

## Agent 分工

| 文档 | Agent 代号 | 角色说明 | 主要信息来源 |
|------|-----------|---------|-------------|
| `00-overview.md` | **Nick Fury** | 总览协调，掌握全局 | `doc/architecture-v2.md` |
| `01-auth.md` | **Black Widow** | 安全认证，身份识别 | 架构文档 Hydra/Login App 章节 |
| `02-frontend.md` | **Spider-Man** | 前端 UI，快速灵活 | 架构文档 Next.js 章节 + legacy 页面功能 |
| `03-bbf-gateway.md` | **Iron Man** | 技术核心，请求编排 | 架构文档 BBF 章节 |
| `04-strapi-data.md` | **Thor** | 强大稳定，数据支柱 | 架构文档 Strapi 章节 + legacy 数据模型 |
| `05-agent-service.md` | **Doctor Strange** | 复杂工作流，异步多维 | 架构文档 Agent 章节 |
| `06-hotel-management.md` | **Captain America** | 核心业务，流程领导 | legacy `HomeController.cs` + 架构文档 |
| `07-room-management.md` | **Hawkeye** | 精准操作，细节把控 | legacy `RoomController.cs` + 架构文档 |
| `08-data-model.md` | **Black Panther** | 技术基础，沉稳严谨 | legacy `ChainDAL.cs` + 架构文档数据层 |
| `09-deployment.md` | **War Machine** | 基础设施，重型支撑 | 架构文档部署章节 |

Spider-Man 专注 `02-frontend.md`，其余 9 位并行撰写各自模块。

---

## 文档写作原则

1. **功能说明部分**：使用步骤列表、截图占位符（`[截图]`）、避免代码，适合运维人员阅读
2. **技术设计部分**：使用 Mermaid 时序图/流程图、接口签名、字段说明，适合开发人员阅读
3. **对照 legacy 系统**：在技术设计中注明与 legacy 实现的主要差异（如从直接 SQL 改为 Strapi API）
4. **不覆盖**：订单管理、账务（Folio）、WorkAcc 相关功能

---

## 输出路径

所有技术文档写入 `/Users/luyun/Documents/poc/ops-ng/doc/` 目录。
