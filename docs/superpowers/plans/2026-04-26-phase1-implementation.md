# ops-ng Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 搭建 ops-ng Phase 1 基础：Podman 基础设施 + Strapi 5 主数据服务 + ORY Hydra SSO + FastAPI BBF 网关，实现完整 OAuth2 授权码流程和酒店/房间 CRUD API。

**Architecture:** 并行构建四个子系统（基础设施、Strapi、Login App、BBF），各自通过 mock 完成单元测试，最后联合集成测试。所有服务通过 podman-compose 运行在同一网络 `ops-ng-net`，BBF 是唯一对外入口。

**Tech Stack:** Podman Compose、Strapi 5 (TypeScript + PostgreSQL)、ORY Hydra、FastAPI (Python 3.11)、PyJWT、httpx、Jinja2、Playwright、pytest、Vitest

---

## 并行流说明

```
Task 1 (基础设施) ──┬── Tasks 2-6  (Thor:  Strapi)        ──┐
                   ├── Tasks 7-11 (BW:    Hydra+LoginApp) ──┤── Tasks 17-18 (集成+e2e)
                   └── Tasks 12-16(IM:    BBF)             ──┘
```

- **Task 1** 所有人依赖，必须最先完成
- **Tasks 2-6、7-11、12-16** 可三个 Agent 并行
- **Tasks 17-18** 需要所有服务就绪

---

## 文件结构总览

```
ops-ng/
├── podman-compose.yml
├── podman-compose.test.yml
├── .env.example
├── scripts/
│   ├── init-db.sh              # 创建 strapi_db / hydra_db
│   └── register-hydra-client.sh
├── strapi/
│   ├── config/
│   │   ├── database.ts
│   │   └── server.ts
│   ├── src/
│   │   ├── index.ts            # bootstrap seed
│   │   └── api/
│   │       ├── hotel/content-types/hotel/schema.json
│   │       ├── room/content-types/room/schema.json
│   │       └── room-type/content-types/room-type/schema.json
│   └── tests/
│       └── hotel.test.ts
├── login-app/
│   ├── main.py
│   ├── routers/
│   │   ├── login.py
│   │   └── consent.py
│   ├── services/
│   │   └── strapi_client.py
│   ├── templates/
│   │   └── login.html
│   ├── tests/
│   │   ├── test_login.py
│   │   └── test_consent.py
│   └── requirements.txt
├── bbf/
│   ├── main.py
│   ├── middleware/
│   │   └── auth.py
│   ├── routers/
│   │   ├── hotels.py
│   │   └── rooms.py
│   ├── services/
│   │   └── strapi_client.py
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_auth.py
│   │   └── test_hotels.py
│   └── requirements.txt
└── e2e/
    ├── package.json
    ├── playwright.config.ts
    └── tests/
        └── sso.spec.ts
```

---

## Task 1: 基础设施 — podman-compose.yml（Nick Fury）

> 依赖：无。其他所有 Task 依赖此 Task。

**Files:**
- Create: `podman-compose.yml`
- Create: `podman-compose.test.yml`
- Create: `.env.example`
- Create: `scripts/init-db.sh`
- Create: `scripts/register-hydra-client.sh`

- [ ] **创建 `.env.example`**

```bash
# .env.example
POSTGRES_USER=ops
POSTGRES_PASSWORD=devpassword123
POSTGRES_HOST=localhost
STRAPI_DB=strapi_db
HYDRA_DB=hydra_db

REDIS_URL=redis://localhost:6379

HYDRA_PUBLIC_URL=http://localhost:4444
HYDRA_ADMIN_URL=http://localhost:4445
HYDRA_SECRETS_SYSTEM=youReallyNeedToChangeThis32chars!!

STRAPI_URL=http://localhost:1337
STRAPI_ADMIN_JWT_SECRET=changeMe32CharsLongSecretForJWT!
STRAPI_APP_KEYS=key1changeMe,key2changeMe
STRAPI_API_TOKEN_SALT=changeMeSaltString

LOGIN_APP_URL=http://localhost:8001
BBF_URL=http://localhost:8000
```

```bash
cp .env.example .env
```

- [ ] **创建 `scripts/init-db.sh`**（PostgreSQL 初始化两个数据库）

```bash
#!/usr/bin/env bash
set -e
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    CREATE DATABASE strapi_db;
    CREATE DATABASE hydra_db;
EOSQL
echo "Databases strapi_db and hydra_db created."
```

```bash
chmod +x scripts/init-db.sh
```

- [ ] **创建 `scripts/register-hydra-client.sh`**

```bash
#!/usr/bin/env bash
set -e
HYDRA_ADMIN=${HYDRA_ADMIN_URL:-http://localhost:4445}

curl -s -X POST "$HYDRA_ADMIN/admin/clients" \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "ops-ng-ui",
    "client_name": "ops-ng UI",
    "grant_types": ["authorization_code", "refresh_token"],
    "response_types": ["code"],
    "scope": "openid offline",
    "redirect_uris": ["http://localhost:3000/callback", "http://localhost:8888/callback"],
    "token_endpoint_auth_method": "none"
  }'
echo "OAuth2 client ops-ng-ui registered."
```

```bash
chmod +x scripts/register-hydra-client.sh
```

- [ ] **创建 `podman-compose.yml`**

```yaml
version: "3.9"

networks:
  ops-ng-net:
    driver: bridge

volumes:
  postgres_data:
  redis_data:

services:
  postgres:
    image: postgres:15-alpine
    restart: unless-stopped
    networks: [ops-ng-net]
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-ops}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-devpassword123}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init-db.sh:/docker-entrypoint-initdb.d/init-db.sh:ro
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-ops}"]
      interval: 5s
      timeout: 5s
      retries: 10

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    networks: [ops-ng-net]
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  hydra-migrate:
    image: oryd/hydra:v2.2.0
    networks: [ops-ng-net]
    command: migrate sql --yes postgres://${POSTGRES_USER:-ops}:${POSTGRES_PASSWORD:-devpassword123}@postgres:5432/${HYDRA_DB:-hydra_db}?sslmode=disable
    depends_on:
      postgres:
        condition: service_healthy

  hydra:
    image: oryd/hydra:v2.2.0
    restart: unless-stopped
    networks: [ops-ng-net]
    command: serve all --dev
    environment:
      DSN: postgres://${POSTGRES_USER:-ops}:${POSTGRES_PASSWORD:-devpassword123}@postgres:5432/${HYDRA_DB:-hydra_db}?sslmode=disable
      URLS_SELF_ISSUER: http://localhost:4444
      URLS_CONSENT: ${LOGIN_APP_URL:-http://localhost:8001}/consent
      URLS_LOGIN: ${LOGIN_APP_URL:-http://localhost:8001}/login
      URLS_LOGOUT: ${LOGIN_APP_URL:-http://localhost:8001}/logout
      SECRETS_SYSTEM: ${HYDRA_SECRETS_SYSTEM:-youReallyNeedToChangeThis32chars!!}
      LOG_LEVEL: info
      OAUTH2_EXPOSE_INTERNAL_ERRORS: "true"
    ports:
      - "4444:4444"
      - "4445:4445"
    depends_on:
      hydra-migrate:
        condition: service_completed_successfully

  strapi:
    build:
      context: ./strapi
      dockerfile: Dockerfile.dev
    restart: unless-stopped
    networks: [ops-ng-net]
    environment:
      DATABASE_CLIENT: postgres
      DATABASE_HOST: postgres
      DATABASE_PORT: 5432
      DATABASE_NAME: ${STRAPI_DB:-strapi_db}
      DATABASE_USERNAME: ${POSTGRES_USER:-ops}
      DATABASE_PASSWORD: ${POSTGRES_PASSWORD:-devpassword123}
      DATABASE_SSL: "false"
      APP_KEYS: ${STRAPI_APP_KEYS:-key1changeMe,key2changeMe}
      API_TOKEN_SALT: ${STRAPI_API_TOKEN_SALT:-changeMeSaltString}
      ADMIN_JWT_SECRET: ${STRAPI_ADMIN_JWT_SECRET:-changeMe32CharsLongSecretForJWT!}
      JWT_SECRET: ${STRAPI_ADMIN_JWT_SECRET:-changeMe32CharsLongSecretForJWT!}
      NODE_ENV: development
    volumes:
      - ./strapi/src:/app/src
      - ./strapi/config:/app/config
    ports:
      - "1337:1337"
    depends_on:
      postgres:
        condition: service_healthy

  login-app:
    build:
      context: ./login-app
      dockerfile: Dockerfile
    restart: unless-stopped
    networks: [ops-ng-net]
    environment:
      HYDRA_ADMIN_URL: http://hydra:4445
      STRAPI_URL: http://strapi:1337
    ports:
      - "8001:8001"
    depends_on:
      - hydra
      - strapi

  bbf:
    build:
      context: ./bbf
      dockerfile: Dockerfile
    restart: unless-stopped
    networks: [ops-ng-net]
    environment:
      HYDRA_PUBLIC_URL: http://hydra:4444
      STRAPI_URL: http://strapi:1337
      STRAPI_SERVICE_TOKEN: ${STRAPI_SERVICE_TOKEN:-}
    ports:
      - "8000:8000"
    depends_on:
      - hydra
      - strapi
```

- [ ] **创建 `podman-compose.test.yml`**（覆盖端口，使用独立数据）

```yaml
version: "3.9"

services:
  postgres:
    environment:
      POSTGRES_USER: ops_test
      POSTGRES_PASSWORD: testpassword
    ports:
      - "5433:5432"

  strapi:
    environment:
      DATABASE_USERNAME: ops_test
      DATABASE_PASSWORD: testpassword
      DATABASE_NAME: strapi_test
      NODE_ENV: test
    ports:
      - "1338:1337"

  hydra:
    ports:
      - "4446:4444"
      - "4447:4445"

  login-app:
    ports:
      - "8002:8001"

  bbf:
    ports:
      - "8080:8000"
```

- [ ] **验证 podman-compose 语法**

```bash
podman-compose -f podman-compose.yml config
```

预期：输出合并后的配置，无报错

- [ ] **启动基础设施（postgres + redis），验证健康**

```bash
podman-compose up -d postgres redis
sleep 5
podman-compose ps
```

预期：postgres 和 redis 状态为 `Up`，healthcheck 为 `healthy`

- [ ] **提交**

```bash
git add podman-compose.yml podman-compose.test.yml .env.example scripts/
git commit -m "feat: add podman-compose infrastructure setup"
```

---

## Task 2: Strapi — 项目初始化（Thor）

> 依赖：Task 1（postgres 运行中）

**Files:**
- Create: `strapi/` (整个项目)
- Create: `strapi/Dockerfile.dev`
- Create: `strapi/config/database.ts`

- [ ] **初始化 Strapi 5 项目**

```bash
cd /Users/luyun/Documents/poc/ops-ng
npx create-strapi-app@latest strapi \
  --no-run \
  --skip-cloud \
  --ts
```

选择：使用默认配置（后续通过环境变量覆盖数据库配置）

- [ ] **覆盖 `strapi/config/database.ts`**（使用环境变量连接 PostgreSQL）

```typescript
// strapi/config/database.ts
import { parse } from "pg-connection-string";

export default ({ env }) => {
  const client = env("DATABASE_CLIENT", "sqlite");

  const connections = {
    postgres: {
      connection: {
        host: env("DATABASE_HOST", "localhost"),
        port: env.int("DATABASE_PORT", 5432),
        database: env("DATABASE_NAME", "strapi_db"),
        user: env("DATABASE_USERNAME", "ops"),
        password: env("DATABASE_PASSWORD", "devpassword123"),
        ssl: env.bool("DATABASE_SSL", false)
          ? { rejectUnauthorized: false }
          : false,
      },
      pool: { min: 2, max: 10 },
    },
  };

  return {
    connection: {
      client,
      ...connections[client],
      acquireConnectionTimeout: env.int("DATABASE_CONNECTION_TIMEOUT", 60000),
    },
  };
};
```

- [ ] **创建 `strapi/Dockerfile.dev`**

```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build
EXPOSE 1337
CMD ["npm", "run", "develop"]
```

- [ ] **本地启动 Strapi 验证连接**（需 Task 1 的 postgres 运行中）

```bash
cd strapi
DATABASE_CLIENT=postgres \
DATABASE_HOST=localhost \
DATABASE_PORT=5432 \
DATABASE_NAME=strapi_db \
DATABASE_USERNAME=ops \
DATABASE_PASSWORD=devpassword123 \
APP_KEYS=key1,key2 \
API_TOKEN_SALT=salt \
ADMIN_JWT_SECRET=secret32charsLongEnoughForJWT! \
JWT_SECRET=secret32charsLongEnoughForJWT! \
npm run develop -- --no-build 2>&1 | head -30
```

预期：看到 `Strapi is running` 或数据库连接成功日志，无 FATAL 错误

- [ ] **提交**

```bash
cd ..
git add strapi/
git commit -m "feat: initialize Strapi 5 project with PostgreSQL config"
```

---

## Task 3: Strapi — Hotel Content Type（Thor）

> 依赖：Task 2

**Files:**
- Create: `strapi/src/api/hotel/content-types/hotel/schema.json`

- [ ] **创建 Hotel schema**

```bash
mkdir -p strapi/src/api/hotel/content-types/hotel
```

```json
{
  "kind": "collectionType",
  "collectionName": "hotels",
  "info": {
    "singularName": "hotel",
    "pluralName": "hotels",
    "displayName": "Hotel",
    "description": "亚朵集团酒店主数据"
  },
  "options": {
    "draftAndPublish": false
  },
  "attributes": {
    "chainId": {
      "type": "integer",
      "unique": true,
      "required": true
    },
    "chainName": {
      "type": "string",
      "required": true,
      "maxLength": 100
    },
    "status": {
      "type": "integer",
      "default": 1
    },
    "step": {
      "type": "integer",
      "default": 0
    },
    "openDate": {
      "type": "datetime"
    },
    "address": {
      "type": "string",
      "maxLength": 200
    },
    "telephone": {
      "type": "string",
      "maxLength": 20
    },
    "cityId": {
      "type": "integer"
    },
    "areaId": {
      "type": "integer"
    },
    "dbName": {
      "type": "string",
      "maxLength": 50
    },
    "instance": {
      "type": "string",
      "maxLength": 50
    },
    "rooms": {
      "type": "relation",
      "relation": "oneToMany",
      "target": "api::room.room",
      "mappedBy": "hotel"
    }
  }
}
```

- [ ] **重启 Strapi，验证 Hotel API 可访问**

```bash
# 在 strapi 目录
npm run develop -- --no-build &
sleep 15
curl -s http://localhost:1337/api/hotels | head -5
```

预期：返回 `{"data":[],"meta":{"pagination":...}}` 或 403（需认证），不应返回 404

- [ ] **提交**

```bash
git add strapi/src/api/hotel/
git commit -m "feat(strapi): add Hotel content type schema"
```

---

## Task 4: Strapi — Room & RoomType Content Types（Thor）

> 依赖：Task 3

**Files:**
- Create: `strapi/src/api/room/content-types/room/schema.json`
- Create: `strapi/src/api/room-type/content-types/room-type/schema.json`

- [ ] **创建 Room schema**

```bash
mkdir -p strapi/src/api/room/content-types/room
```

```json
{
  "kind": "collectionType",
  "collectionName": "rooms",
  "info": {
    "singularName": "room",
    "pluralName": "rooms",
    "displayName": "Room",
    "description": "酒店房间"
  },
  "options": {
    "draftAndPublish": false
  },
  "attributes": {
    "roomNo": {
      "type": "string",
      "required": true,
      "maxLength": 20
    },
    "floor": {
      "type": "integer"
    },
    "hotel": {
      "type": "relation",
      "relation": "manyToOne",
      "target": "api::hotel.hotel",
      "inversedBy": "rooms"
    },
    "roomType": {
      "type": "relation",
      "relation": "manyToOne",
      "target": "api::room-type.room-type",
      "inversedBy": "rooms"
    }
  }
}
```

- [ ] **创建 RoomType schema**

```bash
mkdir -p strapi/src/api/room-type/content-types/room-type
```

```json
{
  "kind": "collectionType",
  "collectionName": "room_types",
  "info": {
    "singularName": "room-type",
    "pluralName": "room-types",
    "displayName": "RoomType",
    "description": "酒店房型"
  },
  "options": {
    "draftAndPublish": false
  },
  "attributes": {
    "roomTypeCode": {
      "type": "string",
      "unique": true,
      "required": true,
      "maxLength": 20
    },
    "roomTypeName": {
      "type": "string",
      "required": true,
      "maxLength": 50
    },
    "bedCount": {
      "type": "integer",
      "default": 1
    },
    "maxCheckInCount": {
      "type": "integer",
      "default": 2
    },
    "sort": {
      "type": "integer",
      "default": 0
    },
    "rooms": {
      "type": "relation",
      "relation": "oneToMany",
      "target": "api::room.room",
      "mappedBy": "roomType"
    }
  }
}
```

- [ ] **重启 Strapi，验证三个 Content Type 均可访问**

```bash
curl -s http://localhost:1337/api/rooms | python3 -c "import sys,json; d=json.load(sys.stdin); print('rooms ok')"
curl -s http://localhost:1337/api/room-types | python3 -c "import sys,json; d=json.load(sys.stdin); print('room-types ok')"
```

预期：两行都打印 `ok`（或 403，不应 404）

- [ ] **提交**

```bash
git add strapi/src/api/room/ strapi/src/api/room-type/
git commit -m "feat(strapi): add Room and RoomType content type schemas"
```

---

## Task 5: Strapi — 权限配置 + API Token + Seed（Thor）

> 依赖：Task 4

**Files:**
- Modify: `strapi/src/index.ts`
- Create: `strapi/scripts/create-tokens.sh`

- [ ] **配置公开权限（通过 Strapi Admin UI 或 bootstrap）**

修改 `strapi/src/index.ts`，在 bootstrap 中设置 API 权限并插入 seed 数据：

```typescript
// strapi/src/index.ts
export default {
  register() {},

  async bootstrap({ strapi }) {
    // 设置 authenticated role 权限（BBF service token 使用）
    const hotelExists = await strapi.db
      .query("api::hotel.hotel")
      .count();

    if (hotelExists === 0) {
      // Seed: 房型
      const rt1 = await strapi.db.query("api::room-type.room-type").create({
        data: { roomTypeCode: "DLX", roomTypeName: "豪华大床房", bedCount: 1, maxCheckInCount: 2, sort: 1 },
      });
      const rt2 = await strapi.db.query("api::room-type.room-type").create({
        data: { roomTypeCode: "TWN", roomTypeName: "标准双床房", bedCount: 2, maxCheckInCount: 3, sort: 2 },
      });
      const rt3 = await strapi.db.query("api::room-type.room-type").create({
        data: { roomTypeCode: "SUT", roomTypeName: "套房", bedCount: 1, maxCheckInCount: 4, sort: 3 },
      });

      // Seed: 酒店 1001
      const hotel1 = await strapi.db.query("api::hotel.hotel").create({
        data: {
          chainId: 1001,
          chainName: "亚朵·测试酒店北京",
          status: 3,
          step: 3,
          cityId: 110000,
          areaId: 110100,
          address: "北京市朝阳区测试路1号",
          telephone: "010-12345678",
        },
      });
      // Seed: 房间（酒店1001）
      for (let i = 1; i <= 5; i++) {
        await strapi.db.query("api::room.room").create({
          data: {
            roomNo: `10${i}`,
            floor: 1,
            hotel: hotel1.id,
            roomType: i <= 3 ? rt1.id : rt2.id,
          },
        });
      }

      // Seed: 酒店 1002
      const hotel2 = await strapi.db.query("api::hotel.hotel").create({
        data: {
          chainId: 1002,
          chainName: "亚朵·测试酒店上海",
          status: 3,
          step: 3,
          cityId: 310000,
          areaId: 310100,
          address: "上海市浦东新区测试路2号",
          telephone: "021-87654321",
        },
      });
      for (let i = 1; i <= 5; i++) {
        await strapi.db.query("api::room.room").create({
          data: {
            roomNo: `20${i}`,
            floor: 2,
            hotel: hotel2.id,
            roomType: i <= 2 ? rt3.id : rt2.id,
          },
        });
      }

      strapi.log.info("Seed data inserted: 2 hotels, 10 rooms, 3 room types");
    }
  },
};
```

- [ ] **重启 Strapi，验证 seed 数据**

```bash
curl -s http://localhost:1337/api/hotels?populate=rooms | \
  python3 -c "import sys,json; d=json.load(sys.stdin); print(f'hotels: {len(d[\"data\"])}')"
```

预期：`hotels: 2`

- [ ] **在 Strapi Admin UI 创建 API Token（BBF 用）**

```bash
# 打开浏览器访问 http://localhost:1337/admin
# Settings > API Tokens > Create new API Token
# Name: bbf-service-token, Type: Full access
# 将生成的 token 保存到 .env: STRAPI_SERVICE_TOKEN=<token>
echo "手动步骤：在 Strapi Admin 创建 API Token 并更新 .env 的 STRAPI_SERVICE_TOKEN"
```

- [ ] **验证 API Token 可用**

```bash
TOKEN=$(grep STRAPI_SERVICE_TOKEN .env | cut -d= -f2)
curl -s -H "Authorization: Bearer $TOKEN" http://localhost:1337/api/hotels | \
  python3 -c "import sys,json; d=json.load(sys.stdin); print(f'authorized: {len(d[\"data\"])} hotels')"
```

预期：`authorized: 2 hotels`

- [ ] **提交**

```bash
git add strapi/src/index.ts
git commit -m "feat(strapi): add seed data and bootstrap setup"
```

---

## Task 6: Strapi — 单元测试（Thor）

> 依赖：Task 5

**Files:**
- Create: `strapi/tests/hotel.test.ts`
- Modify: `strapi/package.json`（添加 vitest 依赖）

- [ ] **安装测试依赖**

```bash
cd strapi
npm install --save-dev vitest @vitest/coverage-v8
```

- [ ] **在 `strapi/package.json` scripts 添加 test 命令**

找到 `"scripts"` 部分，添加：
```json
"test": "vitest run",
"test:watch": "vitest"
```

- [ ] **创建 `strapi/tests/hotel.test.ts`**

```typescript
// strapi/tests/hotel.test.ts
import { describe, it, expect } from "vitest";

// 验证 schema 字段结构（静态验证，不需要运行 Strapi）
import hotelSchema from "../src/api/hotel/content-types/hotel/schema.json";
import roomSchema from "../src/api/room/content-types/room/schema.json";
import roomTypeSchema from "../src/api/room-type/content-types/room-type/schema.json";

describe("Hotel schema", () => {
  it("has required chainId field as unique integer", () => {
    const { chainId } = hotelSchema.attributes;
    expect(chainId.type).toBe("integer");
    expect(chainId.unique).toBe(true);
    expect(chainId.required).toBe(true);
  });

  it("has chainName as required string", () => {
    const { chainName } = hotelSchema.attributes;
    expect(chainName.type).toBe("string");
    expect(chainName.required).toBe(true);
  });

  it("has rooms oneToMany relation", () => {
    const { rooms } = hotelSchema.attributes;
    expect(rooms.type).toBe("relation");
    expect(rooms.relation).toBe("oneToMany");
    expect(rooms.target).toBe("api::room.room");
  });

  it("has status field with default 1", () => {
    expect(hotelSchema.attributes.status.type).toBe("integer");
    expect(hotelSchema.attributes.status.default).toBe(1);
  });
});

describe("Room schema", () => {
  it("has required roomNo field", () => {
    expect(roomSchema.attributes.roomNo.type).toBe("string");
    expect(roomSchema.attributes.roomNo.required).toBe(true);
  });

  it("has manyToOne relation to hotel", () => {
    const { hotel } = roomSchema.attributes;
    expect(hotel.relation).toBe("manyToOne");
    expect(hotel.target).toBe("api::hotel.hotel");
  });

  it("has manyToOne relation to roomType", () => {
    const { roomType } = roomSchema.attributes;
    expect(roomType.relation).toBe("manyToOne");
    expect(roomType.target).toBe("api::room-type.room-type");
  });
});

describe("RoomType schema", () => {
  it("has unique required roomTypeCode", () => {
    const { roomTypeCode } = roomTypeSchema.attributes;
    expect(roomTypeCode.type).toBe("string");
    expect(roomTypeCode.unique).toBe(true);
    expect(roomTypeCode.required).toBe(true);
  });

  it("has bedCount default 1", () => {
    expect(roomTypeSchema.attributes.bedCount.default).toBe(1);
  });
});
```

- [ ] **运行测试，验证通过**

```bash
cd strapi
npm test
```

预期：所有测试 PASS，无 FAIL

- [ ] **提交**

```bash
git add strapi/tests/ strapi/package.json
git commit -m "test(strapi): add schema unit tests"
```

---

## Task 7: ORY Hydra — 配置验证（Black Widow）

> 依赖：Task 1（podman-compose.yml 中的 hydra 服务）

**Files:**
- Create: `scripts/verify-hydra.sh`

- [ ] **启动 Hydra**

```bash
podman-compose up -d postgres hydra-migrate
sleep 10
podman-compose up -d hydra
sleep 5
```

- [ ] **验证 Hydra 健康**

```bash
curl -sf http://localhost:4444/.well-known/openid-configuration | \
  python3 -c "import sys,json; d=json.load(sys.stdin); print('issuer:', d['issuer'])"
```

预期：`issuer: http://localhost:4444`

- [ ] **验证 Hydra Admin 可访问**

```bash
curl -sf http://localhost:4445/admin/clients | python3 -c "import sys,json; print('admin ok, clients:', len(json.load(sys.stdin)))"
```

预期：`admin ok, clients: 0`（无已注册 client）

- [ ] **注册 OAuth2 客户端**

```bash
bash scripts/register-hydra-client.sh
```

预期：打印包含 `client_id: ops-ng-ui` 的 JSON

- [ ] **验证客户端注册成功**

```bash
curl -sf http://localhost:4445/admin/clients/ops-ng-ui | \
  python3 -c "import sys,json; d=json.load(sys.stdin); print('client:', d['client_id'])"
```

预期：`client: ops-ng-ui`

- [ ] **创建 `scripts/verify-hydra.sh`**（供后续集成测试使用）

```bash
#!/usr/bin/env bash
set -e
HYDRA_PUBLIC=${HYDRA_PUBLIC_URL:-http://localhost:4444}
HYDRA_ADMIN=${HYDRA_ADMIN_URL:-http://localhost:4445}

echo "Checking Hydra public endpoint..."
curl -sf "$HYDRA_PUBLIC/.well-known/openid-configuration" > /dev/null
echo "  OK: OIDC discovery"

echo "Checking Hydra admin endpoint..."
curl -sf "$HYDRA_ADMIN/admin/clients" > /dev/null
echo "  OK: Admin API"

echo "Hydra is healthy."
```

```bash
chmod +x scripts/verify-hydra.sh
```

- [ ] **提交**

```bash
git add scripts/verify-hydra.sh
git commit -m "feat: add Hydra verification script"
```

---

## Task 8: Login App — 项目初始化（Black Widow）

> 依赖：Task 7

**Files:**
- Create: `login-app/requirements.txt`
- Create: `login-app/main.py`
- Create: `login-app/Dockerfile`

- [ ] **创建 `login-app/requirements.txt`**

```
fastapi==0.115.0
uvicorn[standard]==0.30.6
httpx==0.27.2
jinja2==3.1.4
python-multipart==0.0.12
pytest==8.3.3
pytest-asyncio==0.24.0
respx==0.21.1
```

- [ ] **创建 `login-app/main.py`**

```python
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from routers import login, consent

app = FastAPI(title="ops-ng Login App")

app.include_router(login.router)
app.include_router(consent.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
```

- [ ] **创建目录结构**

```bash
mkdir -p login-app/routers login-app/services login-app/templates login-app/tests
touch login-app/routers/__init__.py login-app/services/__init__.py login-app/tests/__init__.py
```

- [ ] **创建 `login-app/Dockerfile`**

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8001
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
```

- [ ] **安装依赖，验证启动**

```bash
cd login-app
pip install -r requirements.txt
uvicorn main:app --port 8001 &
sleep 3
curl -sf http://localhost:8001/health
kill %1 2>/dev/null; true
cd ..
```

预期：返回 `{"status":"ok"}`

- [ ] **提交**

```bash
git add login-app/
git commit -m "feat(login-app): initialize FastAPI project"
```

---

## Task 9: Login App — 登录路由（Black Widow）

> 依赖：Task 8

**Files:**
- Create: `login-app/services/strapi_client.py`
- Create: `login-app/services/hydra_client.py`
- Create: `login-app/routers/login.py`
- Create: `login-app/templates/login.html`

- [ ] **创建 `login-app/services/strapi_client.py`**

```python
import os
import httpx

STRAPI_URL = os.getenv("STRAPI_URL", "http://localhost:1337")


async def verify_credentials(identifier: str, password: str) -> dict | None:
    """调用 Strapi /api/auth/local 验证用户凭证。
    返回用户信息 dict，失败返回 None。
    """
    async with httpx.AsyncClient(base_url=STRAPI_URL) as client:
        resp = await client.post(
            "/api/auth/local",
            json={"identifier": identifier, "password": password},
            timeout=10.0,
        )
    if resp.status_code == 200:
        data = resp.json()
        return {
            "id": str(data["user"]["id"]),
            "email": data["user"]["email"],
            "username": data["user"].get("username", identifier),
        }
    return None
```

- [ ] **创建 `login-app/services/hydra_client.py`**

```python
import os
import httpx

HYDRA_ADMIN_URL = os.getenv("HYDRA_ADMIN_URL", "http://localhost:4445")


async def get_login_request(challenge: str) -> dict:
    async with httpx.AsyncClient(base_url=HYDRA_ADMIN_URL) as client:
        resp = await client.get(f"/admin/oauth2/auth/requests/login?login_challenge={challenge}")
        resp.raise_for_status()
        return resp.json()


async def accept_login(challenge: str, subject: str) -> str:
    """接受登录请求，返回 Hydra 要求的 redirect_to URL。"""
    async with httpx.AsyncClient(base_url=HYDRA_ADMIN_URL) as client:
        resp = await client.put(
            f"/admin/oauth2/auth/requests/login/accept?login_challenge={challenge}",
            json={"subject": subject, "remember": False, "remember_for": 0},
        )
        resp.raise_for_status()
        return resp.json()["redirect_to"]


async def get_consent_request(challenge: str) -> dict:
    async with httpx.AsyncClient(base_url=HYDRA_ADMIN_URL) as client:
        resp = await client.get(f"/admin/oauth2/auth/requests/consent?consent_challenge={challenge}")
        resp.raise_for_status()
        return resp.json()


async def accept_consent(challenge: str, subject: str, requested_scope: list[str]) -> str:
    """自动接受 consent，返回 redirect_to URL。"""
    async with httpx.AsyncClient(base_url=HYDRA_ADMIN_URL) as client:
        resp = await client.put(
            f"/admin/oauth2/auth/requests/consent/accept?consent_challenge={challenge}",
            json={
                "grant_scope": requested_scope,
                "grant_access_token_audience": [],
                "session": {
                    "access_token": {"sub": subject},
                    "id_token": {"sub": subject},
                },
            },
        )
        resp.raise_for_status()
        return resp.json()["redirect_to"]
```

- [ ] **创建 `login-app/templates/login.html`**

```html
<!DOCTYPE html>
<html lang="zh">
<head>
  <meta charset="UTF-8">
  <title>ops-ng 登录</title>
  <style>
    body { font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; background: #f5f5f5; }
    .card { background: white; padding: 2rem; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); width: 320px; }
    h1 { font-size: 1.5rem; margin-bottom: 1.5rem; color: #333; }
    input { width: 100%; padding: 0.5rem; margin-bottom: 1rem; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
    button { width: 100%; padding: 0.75rem; background: #1a1a2e; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 1rem; }
    button:hover { background: #16213e; }
    .error { color: #e74c3c; margin-bottom: 1rem; font-size: 0.9rem; }
  </style>
</head>
<body>
  <div class="card">
    <h1>亚朵运维系统</h1>
    {% if error %}
    <div class="error">{{ error }}</div>
    {% endif %}
    <form method="post" action="/login">
      <input type="hidden" name="login_challenge" value="{{ login_challenge }}">
      <input type="text" name="identifier" placeholder="邮箱 / 用户名" required autofocus>
      <input type="password" name="password" placeholder="密码" required>
      <button type="submit">登录</button>
    </form>
  </div>
</body>
</html>
```

- [ ] **创建 `login-app/routers/login.py`**

```python
import os
from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from services.strapi_client import verify_credentials
from services.hydra_client import get_login_request, accept_login

router = APIRouter()
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "../templates"))


@router.get("/login", response_class=HTMLResponse)
async def login_form(request: Request, login_challenge: str):
    # 验证 challenge 有效
    await get_login_request(login_challenge)
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "login_challenge": login_challenge, "error": None},
    )


@router.post("/login", response_class=HTMLResponse)
async def login_submit(
    request: Request,
    login_challenge: str = Form(...),
    identifier: str = Form(...),
    password: str = Form(...),
):
    user = await verify_credentials(identifier, password)
    if user is None:
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "login_challenge": login_challenge,
                "error": "账号或密码错误，请重试",
            },
            status_code=401,
        )
    redirect_to = await accept_login(login_challenge, subject=user["id"])
    return RedirectResponse(redirect_to, status_code=302)
```

- [ ] **提交**

```bash
git add login-app/
git commit -m "feat(login-app): add login routes and Hydra/Strapi clients"
```

---

## Task 10: Login App — Consent 路由（Black Widow）

> 依赖：Task 9

**Files:**
- Create: `login-app/routers/consent.py`

- [ ] **创建 `login-app/routers/consent.py`**

```python
from fastapi import APIRouter
from fastapi.responses import RedirectResponse

from services.hydra_client import get_consent_request, accept_consent

router = APIRouter()


@router.get("/consent")
async def consent(consent_challenge: str):
    consent_req = await get_consent_request(consent_challenge)
    subject = consent_req.get("subject", "")
    requested_scope = consent_req.get("requested_scope", [])

    redirect_to = await accept_consent(
        challenge=consent_challenge,
        subject=subject,
        requested_scope=requested_scope,
    )
    return RedirectResponse(redirect_to, status_code=302)


@router.get("/logout")
async def logout():
    # Phase 1: 简单返回成功，不做 Hydra logout 处理
    return {"status": "logged out"}
```

- [ ] **本地启动 Login App 验证路由注册**

```bash
cd login-app
uvicorn main:app --port 8001 &
sleep 3
curl -sf http://localhost:8001/health
curl -s http://localhost:8001/login 2>&1 | grep -c "login_challenge" || echo "missing challenge param (expected)"
kill %1 2>/dev/null; true
cd ..
```

预期：health 返回 ok；/login 不带 challenge 参数时返回 422 或错误（说明路由已注册）

- [ ] **提交**

```bash
git add login-app/routers/consent.py
git commit -m "feat(login-app): add consent and logout routes"
```

---

## Task 11: Login App — 单元测试（Black Widow）

> 依赖：Task 10

**Files:**
- Create: `login-app/tests/test_login.py`
- Create: `login-app/tests/test_consent.py`
- Create: `login-app/pytest.ini`

- [ ] **创建 `login-app/pytest.ini`**

```ini
[pytest]
asyncio_mode = auto
```

- [ ] **创建 `login-app/tests/test_login.py`**

```python
import pytest
import respx
import httpx
from fastapi.testclient import TestClient

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from main import app

client = TestClient(app, raise_server_exceptions=False)

STRAPI_URL = "http://localhost:1337"
HYDRA_ADMIN_URL = "http://localhost:4445"


@respx.mock
def test_login_form_renders_with_valid_challenge():
    """GET /login?login_challenge=xxx 应返回 HTML 表单"""
    respx.get(f"{HYDRA_ADMIN_URL}/admin/oauth2/auth/requests/login").mock(
        return_value=httpx.Response(200, json={"challenge": "test-challenge", "subject": ""})
    )
    resp = client.get("/login?login_challenge=test-challenge", follow_redirects=False)
    assert resp.status_code == 200
    assert "亚朵运维系统" in resp.text
    assert 'name="login_challenge"' in resp.text


@respx.mock
def test_login_post_valid_credentials_redirects():
    """POST /login 凭证正确，应重定向到 Hydra redirect_to"""
    respx.post(f"{STRAPI_URL}/api/auth/local").mock(
        return_value=httpx.Response(200, json={
            "jwt": "fake-jwt",
            "user": {"id": 1, "email": "test@yaduo.com", "username": "testuser"},
        })
    )
    respx.put(f"{HYDRA_ADMIN_URL}/admin/oauth2/auth/requests/login/accept").mock(
        return_value=httpx.Response(200, json={"redirect_to": "http://localhost:4444/oauth2/auth?consent_challenge=abc"})
    )
    resp = client.post(
        "/login",
        data={"login_challenge": "test-challenge", "identifier": "test@yaduo.com", "password": "correct"},
        follow_redirects=False,
    )
    assert resp.status_code == 302
    assert "consent_challenge" in resp.headers["location"]


@respx.mock
def test_login_post_invalid_credentials_returns_401():
    """POST /login 凭证错误，应返回 401 并显示错误信息"""
    respx.post(f"{STRAPI_URL}/api/auth/local").mock(
        return_value=httpx.Response(400, json={"error": {"message": "Invalid identifier or password"}})
    )
    resp = client.post(
        "/login",
        data={"login_challenge": "test-challenge", "identifier": "bad@test.com", "password": "wrong"},
        follow_redirects=False,
    )
    assert resp.status_code == 401
    assert "账号或密码错误" in resp.text
```

- [ ] **运行测试，验证失败**

```bash
cd login-app
pytest tests/test_login.py -v
```

预期：所有测试 PASS（已有实现），或如有错误修正代码直到全通过

- [ ] **创建 `login-app/tests/test_consent.py`**

```python
import respx
import httpx
from fastapi.testclient import TestClient

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from main import app

client = TestClient(app, raise_server_exceptions=False)

HYDRA_ADMIN_URL = "http://localhost:4445"


@respx.mock
def test_consent_auto_accepts_and_redirects():
    """GET /consent?consent_challenge=xxx 应自动接受并重定向"""
    respx.get(f"{HYDRA_ADMIN_URL}/admin/oauth2/auth/requests/consent").mock(
        return_value=httpx.Response(200, json={
            "challenge": "consent-challenge",
            "subject": "1",
            "requested_scope": ["openid", "offline"],
        })
    )
    respx.put(f"{HYDRA_ADMIN_URL}/admin/oauth2/auth/requests/consent/accept").mock(
        return_value=httpx.Response(200, json={"redirect_to": "http://localhost:3000/callback?code=authcode123"})
    )
    resp = client.get("/consent?consent_challenge=consent-challenge", follow_redirects=False)
    assert resp.status_code == 302
    assert "code=authcode123" in resp.headers["location"]


def test_logout_returns_ok():
    resp = client.get("/logout")
    assert resp.status_code == 200
    assert resp.json()["status"] == "logged out"
```

- [ ] **运行全部测试**

```bash
pytest tests/ -v
```

预期：全部 PASS

- [ ] **提交**

```bash
git add login-app/tests/ login-app/pytest.ini
git commit -m "test(login-app): add unit tests for login and consent routes"
```

---

## Task 12: BBF — 项目初始化（Iron Man）

> 依赖：Task 1

**Files:**
- Create: `bbf/requirements.txt`
- Create: `bbf/main.py`
- Create: `bbf/Dockerfile`

- [ ] **创建 `bbf/requirements.txt`**

```
fastapi==0.115.0
uvicorn[standard]==0.30.6
httpx==0.27.2
PyJWT[crypto]==2.9.0
cryptography==43.0.3
pytest==8.3.3
pytest-asyncio==0.24.0
respx==0.21.1
```

- [ ] **创建目录结构**

```bash
mkdir -p bbf/middleware bbf/routers bbf/services bbf/tests
touch bbf/middleware/__init__.py bbf/routers/__init__.py bbf/services/__init__.py bbf/tests/__init__.py
```

- [ ] **创建 `bbf/main.py`**

```python
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import hotels, rooms

app = FastAPI(title="ops-ng BBF Gateway")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(hotels.router, prefix="/api")
app.include_router(rooms.router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok"}
```

- [ ] **创建 `bbf/Dockerfile`**

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **安装依赖，验证启动**

```bash
cd bbf
pip install -r requirements.txt
uvicorn main:app --port 8000 &
sleep 3
curl -sf http://localhost:8000/health
kill %1 2>/dev/null; true
cd ..
```

预期：返回 `{"status":"ok"}`

- [ ] **提交**

```bash
git add bbf/
git commit -m "feat(bbf): initialize FastAPI BBF project"
```

---

## Task 13: BBF — JWT 验证中间件（Iron Man）

> 依赖：Task 12

**Files:**
- Create: `bbf/middleware/auth.py`
- Modify: `bbf/main.py`

- [ ] **创建 `bbf/middleware/auth.py`**

```python
import os
import time
from typing import Optional

import httpx
import jwt
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from jwt import PyJWKClient, PyJWKClientError

HYDRA_PUBLIC_URL = os.getenv("HYDRA_PUBLIC_URL", "http://localhost:4444")
JWKS_URI = f"{HYDRA_PUBLIC_URL}/.well-known/jwks.json"

# JWKS 缓存
_jwks_client: Optional[PyJWKClient] = None
_jwks_cache_time: float = 0
JWKS_CACHE_TTL = 3600  # 1 hour


def get_jwks_client() -> PyJWKClient:
    global _jwks_client, _jwks_cache_time
    now = time.time()
    if _jwks_client is None or (now - _jwks_cache_time) > JWKS_CACHE_TTL:
        _jwks_client = PyJWKClient(JWKS_URI)
        _jwks_cache_time = now
    return _jwks_client


def error_response(message: str, code: str, status: int = 401):
    return JSONResponse(
        status_code=status,
        content={"error": message, "code": code},
    )


SKIP_AUTH_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}


async def jwt_auth_middleware(request: Request, call_next):
    if request.url.path in SKIP_AUTH_PATHS:
        return await call_next(request)

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return error_response("Missing or invalid Authorization header", "MISSING_TOKEN")

    token = auth_header[len("Bearer "):]

    try:
        jwks_client = get_jwks_client()
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            options={"verify_aud": False},
        )
        request.state.user_id = payload.get("sub", "")
        request.state.token_payload = payload
    except jwt.ExpiredSignatureError:
        return error_response("Token has expired", "TOKEN_EXPIRED")
    except (jwt.InvalidTokenError, PyJWKClientError) as e:
        return error_response(f"Invalid token: {str(e)}", "INVALID_TOKEN")

    return await call_next(request)
```

- [ ] **注册中间件到 `bbf/main.py`**

在 `app.add_middleware(CORSMiddleware, ...)` 下方添加：

```python
from middleware.auth import jwt_auth_middleware
from starlette.middleware.base import BaseHTTPMiddleware

app.add_middleware(BaseHTTPMiddleware, dispatch=jwt_auth_middleware)
```

- [ ] **提交**

```bash
git add bbf/middleware/ bbf/main.py
git commit -m "feat(bbf): add JWT auth middleware with JWKS caching"
```

---

## Task 14: BBF — Hotel 路由（Iron Man）

> 依赖：Task 13

**Files:**
- Create: `bbf/services/strapi_client.py`
- Create: `bbf/routers/hotels.py`

- [ ] **创建 `bbf/services/strapi_client.py`**

```python
import os
import httpx

STRAPI_URL = os.getenv("STRAPI_URL", "http://localhost:1337")
STRAPI_SERVICE_TOKEN = os.getenv("STRAPI_SERVICE_TOKEN", "")


def _auth_headers() -> dict:
    return {"Authorization": f"Bearer {STRAPI_SERVICE_TOKEN}"} if STRAPI_SERVICE_TOKEN else {}


async def strapi_get(path: str, params: dict = None) -> httpx.Response:
    async with httpx.AsyncClient(base_url=STRAPI_URL, headers=_auth_headers()) as client:
        return await client.get(path, params=params, timeout=10.0)


async def strapi_post(path: str, data: dict) -> httpx.Response:
    async with httpx.AsyncClient(base_url=STRAPI_URL, headers=_auth_headers()) as client:
        return await client.post(path, json={"data": data}, timeout=10.0)


async def strapi_put(path: str, data: dict) -> httpx.Response:
    async with httpx.AsyncClient(base_url=STRAPI_URL, headers=_auth_headers()) as client:
        return await client.put(path, json={"data": data}, timeout=10.0)
```

- [ ] **创建 `bbf/routers/hotels.py`**

```python
from fastapi import APIRouter, Request, Query, HTTPException
from fastapi.responses import JSONResponse

from services.strapi_client import strapi_get, strapi_post, strapi_put

router = APIRouter()


@router.get("/hotels")
async def list_hotels(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    chain_name: str = Query(None),
):
    params = {
        "pagination[page]": page,
        "pagination[pageSize]": page_size,
    }
    if chain_name:
        params["filters[chainName][$containsi]"] = chain_name

    resp = await strapi_get("/api/hotels", params=params)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="Strapi error")
    return resp.json()


@router.get("/hotels/{hotel_id}")
async def get_hotel(hotel_id: int):
    resp = await strapi_get(f"/api/hotels/{hotel_id}")
    if resp.status_code == 404:
        raise HTTPException(status_code=404, detail="Hotel not found")
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="Strapi error")
    return resp.json()


@router.post("/hotels")
async def create_hotel(request: Request):
    body = await request.json()
    resp = await strapi_post("/api/hotels", body)
    if resp.status_code not in (200, 201):
        raise HTTPException(status_code=resp.status_code, detail="Strapi error")
    return JSONResponse(content=resp.json(), status_code=201)


@router.put("/hotels/{hotel_id}")
async def update_hotel(hotel_id: int, request: Request):
    body = await request.json()
    resp = await strapi_put(f"/api/hotels/{hotel_id}", body)
    if resp.status_code == 404:
        raise HTTPException(status_code=404, detail="Hotel not found")
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="Strapi error")
    return resp.json()
```

- [ ] **提交**

```bash
git add bbf/services/ bbf/routers/hotels.py
git commit -m "feat(bbf): add hotel routes with Strapi proxy"
```

---

## Task 15: BBF — Room 路由（Iron Man）

> 依赖：Task 14

**Files:**
- Create: `bbf/routers/rooms.py`

- [ ] **创建 `bbf/routers/rooms.py`**

```python
from fastapi import APIRouter, Query, HTTPException

from services.strapi_client import strapi_get

router = APIRouter()


@router.get("/hotels/{hotel_id}/rooms")
async def list_hotel_rooms(
    hotel_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
):
    params = {
        "filters[hotel][id][$eq]": hotel_id,
        "populate": "roomType",
        "pagination[page]": page,
        "pagination[pageSize]": page_size,
    }
    resp = await strapi_get("/api/rooms", params=params)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="Strapi error")
    return resp.json()
```

- [ ] **提交**

```bash
git add bbf/routers/rooms.py
git commit -m "feat(bbf): add room routes"
```

---

## Task 16: BBF — 单元测试（Iron Man）

> 依赖：Task 15

**Files:**
- Create: `bbf/tests/conftest.py`
- Create: `bbf/tests/test_auth.py`
- Create: `bbf/tests/test_hotels.py`
- Create: `bbf/pytest.ini`

- [ ] **创建 `bbf/pytest.ini`**

```ini
[pytest]
asyncio_mode = auto
```

- [ ] **生成测试用 RSA 密钥对**（用于 JWT 测试）

```bash
cd bbf
python3 -c "
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
priv = key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.TraditionalOpenSSL, serialization.NoEncryption())
pub = key.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
print('PRIVATE_KEY =', repr(priv.decode()))
print('PUBLIC_KEY =', repr(pub.decode()))
" > tests/_keys.py
cd ..
```

- [ ] **创建 `bbf/tests/conftest.py`**

```python
import pytest
import jwt
import time
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from fastapi.testclient import TestClient

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


@pytest.fixture(scope="session")
def rsa_private_key():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return key


@pytest.fixture(scope="session")
def rsa_public_key(rsa_private_key):
    return rsa_private_key.public_key()


@pytest.fixture(scope="session")
def valid_token(rsa_private_key):
    priv_pem = rsa_private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.TraditionalOpenSSL,
        serialization.NoEncryption(),
    )
    payload = {
        "sub": "user-123",
        "iss": "http://localhost:4444",
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,
        "scp": ["openid", "offline"],
    }
    return jwt.encode(payload, priv_pem, algorithm="RS256")


@pytest.fixture(scope="session")
def expired_token(rsa_private_key):
    priv_pem = rsa_private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.TraditionalOpenSSL,
        serialization.NoEncryption(),
    )
    payload = {
        "sub": "user-123",
        "iss": "http://localhost:4444",
        "iat": int(time.time()) - 7200,
        "exp": int(time.time()) - 3600,  # 已过期
    }
    return jwt.encode(payload, priv_pem, algorithm="RS256")
```

- [ ] **创建 `bbf/tests/test_auth.py`**

```python
import pytest
import respx
import httpx
import json
import base64
from unittest.mock import patch
from cryptography.hazmat.primitives import serialization
from fastapi.testclient import TestClient

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from main import app

client = TestClient(app, raise_server_exceptions=False)


def test_health_no_auth_required():
    resp = client.get("/health")
    assert resp.status_code == 200


def test_missing_token_returns_401():
    resp = client.get("/api/hotels")
    assert resp.status_code == 401
    assert resp.json()["code"] == "MISSING_TOKEN"


def test_invalid_bearer_format_returns_401():
    resp = client.get("/api/hotels", headers={"Authorization": "Basic abc123"})
    assert resp.status_code == 401
    assert resp.json()["code"] == "MISSING_TOKEN"


def test_expired_token_returns_401(expired_token, rsa_public_key):
    pub_pem = rsa_public_key.public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    with patch("middleware.auth.get_jwks_client") as mock_get_client:
        mock_signing_key = type("Key", (), {"key": pub_pem})()
        mock_client = type("Client", (), {"get_signing_key_from_jwt": lambda s, t: mock_signing_key})()
        mock_get_client.return_value = mock_client
        resp = client.get("/api/hotels", headers={"Authorization": f"Bearer {expired_token}"})
    assert resp.status_code == 401
    assert resp.json()["code"] == "TOKEN_EXPIRED"


@respx.mock
def test_valid_token_passes_to_strapi(valid_token, rsa_public_key):
    pub_pem = rsa_public_key.public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    respx.get("http://localhost:1337/api/hotels").mock(
        return_value=httpx.Response(200, json={"data": [], "meta": {"pagination": {"page": 1, "pageSize": 25, "total": 0}}})
    )
    with patch("middleware.auth.get_jwks_client") as mock_get_client:
        mock_signing_key = type("Key", (), {"key": pub_pem})()
        mock_client = type("Client", (), {"get_signing_key_from_jwt": lambda s, t: mock_signing_key})()
        mock_get_client.return_value = mock_client
        resp = client.get("/api/hotels", headers={"Authorization": f"Bearer {valid_token}"})
    assert resp.status_code == 200
```

- [ ] **创建 `bbf/tests/test_hotels.py`**

```python
import pytest
import respx
import httpx
from unittest.mock import patch
from cryptography.hazmat.primitives import serialization
from fastapi.testclient import TestClient

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from main import app

client = TestClient(app, raise_server_exceptions=False)

STRAPI_URL = "http://localhost:1337"

HOTEL_RESPONSE = {
    "data": [
        {"id": 1, "attributes": {"chainId": 1001, "chainName": "亚朵·测试北京", "status": 3}},
        {"id": 2, "attributes": {"chainId": 1002, "chainName": "亚朵·测试上海", "status": 3}},
    ],
    "meta": {"pagination": {"page": 1, "pageSize": 25, "total": 2}},
}


def _mock_auth(valid_token, rsa_public_key):
    pub_pem = rsa_public_key.public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    mock_signing_key = type("Key", (), {"key": pub_pem})()
    mock_client = type("Client", (), {"get_signing_key_from_jwt": lambda s, t: mock_signing_key})()
    return patch("middleware.auth.get_jwks_client", return_value=mock_client)


@respx.mock
def test_list_hotels_returns_strapi_data(valid_token, rsa_public_key):
    respx.get(f"{STRAPI_URL}/api/hotels").mock(
        return_value=httpx.Response(200, json=HOTEL_RESPONSE)
    )
    with _mock_auth(valid_token, rsa_public_key):
        resp = client.get("/api/hotels", headers={"Authorization": f"Bearer {valid_token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["data"]) == 2
    assert data["data"][0]["attributes"]["chainId"] == 1001


@respx.mock
def test_get_hotel_not_found(valid_token, rsa_public_key):
    respx.get(f"{STRAPI_URL}/api/hotels/999").mock(
        return_value=httpx.Response(404, json={"error": {"message": "Not Found"}})
    )
    with _mock_auth(valid_token, rsa_public_key):
        resp = client.get("/api/hotels/999", headers={"Authorization": f"Bearer {valid_token}"})
    assert resp.status_code == 404


@respx.mock
def test_create_hotel(valid_token, rsa_public_key):
    respx.post(f"{STRAPI_URL}/api/hotels").mock(
        return_value=httpx.Response(200, json={"data": {"id": 3, "attributes": {"chainId": 1003}}})
    )
    with _mock_auth(valid_token, rsa_public_key):
        resp = client.post(
            "/api/hotels",
            json={"chainId": 1003, "chainName": "亚朵·测试广州"},
            headers={"Authorization": f"Bearer {valid_token}"},
        )
    assert resp.status_code == 201
```

- [ ] **运行 BBF 全部测试**

```bash
cd bbf
pytest tests/ -v
```

预期：全部 PASS

- [ ] **提交**

```bash
git add bbf/tests/ bbf/pytest.ini
git commit -m "test(bbf): add JWT auth and hotel route unit tests"
```

---

## Task 17: 集成 — 全链路冒烟测试（Nick Fury）

> 依赖：Tasks 2-16（所有服务已构建）

**Files:**
- Create: `scripts/smoke-test.sh`

- [ ] **启动全部服务**

```bash
podman-compose up -d
sleep 30
podman-compose ps
```

预期：所有服务状态为 `Up`

- [ ] **验证各服务健康**

```bash
curl -sf http://localhost:1337/api/hotels -o /dev/null && echo "Strapi OK"
curl -sf http://localhost:4444/.well-known/openid-configuration -o /dev/null && echo "Hydra OK"
curl -sf http://localhost:8001/health && echo "Login App OK"
curl -s http://localhost:8000/health && echo "BBF OK"
```

预期：四行均输出 OK

- [ ] **验证 BBF 未授权拦截**

```bash
STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/hotels)
[ "$STATUS" = "401" ] && echo "401 OK" || echo "FAIL: got $STATUS"
```

预期：`401 OK`

- [ ] **执行完整 OAuth2 授权码流程（手动步骤）**

```bash
# 1. 构造授权 URL（PKCE 简化验证）
CODE_VERIFIER=$(openssl rand -base64 32 | tr -d '+=/' | cut -c1-43)
CODE_CHALLENGE=$(echo -n "$CODE_VERIFIER" | sha256sum | xxd -r -p | base64 | tr -d '=' | tr '+/' '-_')

AUTH_URL="http://localhost:4444/oauth2/auth?client_id=ops-ng-ui&response_type=code&scope=openid+offline&redirect_uri=http://localhost:8888/callback&code_challenge=$CODE_CHALLENGE&code_challenge_method=S256&state=teststate"

echo "请在浏览器打开以下 URL 完成登录流程："
echo "$AUTH_URL"
echo ""
echo "登录后，从 redirect URL 中提取 code 参数，赋值到 AUTH_CODE 变量："
echo 'read -p "AUTH_CODE=" AUTH_CODE'
```

- [ ] **用 code 换取 Access Token**

```bash
# 在上一步获取 AUTH_CODE 后执行：
TOKEN_RESP=$(curl -s -X POST http://localhost:4444/oauth2/token \
  -d "grant_type=authorization_code&code=$AUTH_CODE&redirect_uri=http://localhost:8888/callback&client_id=ops-ng-ui&code_verifier=$CODE_VERIFIER")

ACCESS_TOKEN=$(echo $TOKEN_RESP | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
echo "Access Token 获取成功: ${ACCESS_TOKEN:0:20}..."
```

- [ ] **用 Access Token 访问 BBF**

```bash
curl -s -H "Authorization: Bearer $ACCESS_TOKEN" http://localhost:8000/api/hotels | \
  python3 -c "import sys,json; d=json.load(sys.stdin); print(f'hotels: {len(d[\"data\"])}')"
```

预期：`hotels: 2`

- [ ] **创建 `scripts/smoke-test.sh`**（自动化非 OAuth 部分）

```bash
#!/usr/bin/env bash
set -e
echo "=== ops-ng Phase 1 Smoke Test ==="

echo "1. Checking service health..."
curl -sf http://localhost:1337/api/hotels -o /dev/null && echo "  Strapi: OK"
curl -sf http://localhost:4444/.well-known/openid-configuration -o /dev/null && echo "  Hydra: OK"
curl -sf http://localhost:8001/health -o /dev/null && echo "  Login App: OK"
curl -sf http://localhost:8000/health -o /dev/null && echo "  BBF: OK"

echo "2. Checking BBF auth enforcement..."
STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/hotels)
[ "$STATUS" = "401" ] && echo "  BBF unauthenticated: 401 OK" || (echo "  FAIL: expected 401, got $STATUS"; exit 1)

echo "3. Checking Strapi seed data..."
TOKEN="${STRAPI_SERVICE_TOKEN:-}"
if [ -n "$TOKEN" ]; then
  COUNT=$(curl -sf -H "Authorization: Bearer $TOKEN" "http://localhost:1337/api/hotels" | \
    python3 -c "import sys,json; print(json.load(sys.stdin)['meta']['pagination']['total'])")
  [ "$COUNT" -ge "2" ] && echo "  Strapi seed: $COUNT hotels OK" || echo "  WARNING: only $COUNT hotels"
fi

echo "=== Smoke test passed ==="
```

```bash
chmod +x scripts/smoke-test.sh
bash scripts/smoke-test.sh
```

- [ ] **提交**

```bash
git add scripts/smoke-test.sh
git commit -m "feat: add smoke test script for Phase 1 integration"
```

---

## Task 18: e2e 测试 — Playwright SSO 流程（Nick Fury）

> 依赖：Task 17（所有服务运行中）

**Files:**
- Create: `e2e/package.json`
- Create: `e2e/playwright.config.ts`
- Create: `e2e/tests/sso.spec.ts`

- [ ] **初始化 e2e 目录**

```bash
mkdir -p e2e/tests
cd e2e
npm init -y
npm install --save-dev @playwright/test
npx playwright install chromium
cd ..
```

- [ ] **创建 `e2e/playwright.config.ts`**

```typescript
import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  timeout: 30_000,
  retries: 1,
  use: {
    baseURL: "http://localhost:8000",
    headless: true,
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
  },
  reporter: "list",
});
```

- [ ] **创建 `e2e/tests/sso.spec.ts`**

```typescript
import { test, expect, chromium } from "@playwright/test";
import * as crypto from "crypto";

const HYDRA_URL = "http://localhost:4444";
const BBF_URL = "http://localhost:8000";
const LOGIN_APP_URL = "http://localhost:8001";
const STRAPI_URL = "http://localhost:1337";

// 测试账号（需在 Strapi 中已创建）
const TEST_USER = "test@yaduo.com";
const TEST_PASSWORD = "Test@123456";

function generatePKCE() {
  const verifier = crypto.randomBytes(32).toString("base64url");
  const challenge = crypto
    .createHash("sha256")
    .update(verifier)
    .digest("base64url");
  return { verifier, challenge };
}

test.describe("SSO 完整登录流程", () => {
  test("应能完成 OAuth2 授权码流程并获取 Access Token", async ({ page }) => {
    const { verifier, challenge } = generatePKCE();
    const state = "e2e-test-state";
    const redirectUri = "http://localhost:8888/callback";

    const authUrl =
      `${HYDRA_URL}/oauth2/auth?client_id=ops-ng-ui` +
      `&response_type=code&scope=openid+offline` +
      `&redirect_uri=${encodeURIComponent(redirectUri)}` +
      `&code_challenge=${challenge}&code_challenge_method=S256` +
      `&state=${state}`;

    // 1. 访问授权 URL，Hydra 跳转至 Login App
    await page.goto(authUrl);
    await expect(page).toHaveURL(/localhost:8001\/login/);
    await expect(page.locator("h1")).toContainText("亚朵运维系统");

    // 2. 填写凭证提交登录
    await page.fill('input[name="identifier"]', TEST_USER);
    await page.fill('input[name="password"]', TEST_PASSWORD);
    await page.click('button[type="submit"]');

    // 3. Login App 处理 consent 后应跳转到 redirect_uri（含 code 参数）
    // 由于没有真实的 localhost:8888 服务，等待跳转失败并从 URL 提取 code
    await page.waitForURL(/localhost:8888\/callback/, { timeout: 10_000 }).catch(() => {});
    const url = new URL(page.url());
    const code = url.searchParams.get("code");
    const returnedState = url.searchParams.get("state");

    expect(code).toBeTruthy();
    expect(returnedState).toBe(state);

    // 4. 用 code 换取 Access Token
    const tokenResp = await fetch(`${HYDRA_URL}/oauth2/token`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({
        grant_type: "authorization_code",
        code: code!,
        redirect_uri: redirectUri,
        client_id: "ops-ng-ui",
        code_verifier: verifier,
      }),
    });
    expect(tokenResp.status).toBe(200);
    const tokenData = await tokenResp.json();
    expect(tokenData.access_token).toBeTruthy();

    // 5. 用 Access Token 访问 BBF API
    const apiResp = await fetch(`${BBF_URL}/api/hotels`, {
      headers: { Authorization: `Bearer ${tokenData.access_token}` },
    });
    expect(apiResp.status).toBe(200);
    const apiData = await apiResp.json();
    expect(Array.isArray(apiData.data)).toBe(true);
  });

  test("无 Token 访问 BBF 应返回 401", async ({ request }) => {
    const resp = await request.get(`${BBF_URL}/api/hotels`);
    expect(resp.status()).toBe(401);
    const body = await resp.json();
    expect(body.code).toBe("MISSING_TOKEN");
  });

  test("错误密码登录应显示错误提示", async ({ page }) => {
    const { challenge } = generatePKCE();
    const authUrl =
      `${HYDRA_URL}/oauth2/auth?client_id=ops-ng-ui` +
      `&response_type=code&scope=openid+offline` +
      `&redirect_uri=${encodeURIComponent("http://localhost:8888/callback")}` +
      `&code_challenge=${challenge}&code_challenge_method=S256&state=test`;

    await page.goto(authUrl);
    await expect(page).toHaveURL(/localhost:8001\/login/);

    await page.fill('input[name="identifier"]', "wrong@test.com");
    await page.fill('input[name="password"]', "wrongpassword");
    await page.click('button[type="submit"]');

    // 保持在登录页，显示错误
    await expect(page).toHaveURL(/localhost:8001\/login/);
    await expect(page.locator(".error")).toContainText("账号或密码错误");
  });
});
```

- [ ] **在 Strapi Admin 中创建测试用户**

```bash
echo "手动步骤：在 Strapi Admin (http://localhost:1337/admin) 创建用户："
echo "  Email: test@yaduo.com"
echo "  Password: Test@123456"
echo "  Role: Authenticated"
echo "  Confirmed: true"
```

- [ ] **运行 e2e 测试**

```bash
cd e2e
npx playwright test
```

预期：3 个测试全部 PASS（或第一个因缺少测试用户而 FAIL，先补充用户再重跑）

- [ ] **提交**

```bash
git add e2e/
git commit -m "test(e2e): add Playwright SSO end-to-end tests"
```

---

## Phase 1 验收清单

运行以下命令验证 Phase 1 完成标准：

```bash
# 1. 基础设施健康
bash scripts/smoke-test.sh

# 2. Strapi 单元测试
cd strapi && npm test && cd ..

# 3. Login App 单元测试
cd login-app && pytest tests/ -v && cd ..

# 4. BBF 单元测试
cd bbf && pytest tests/ -v && cd ..

# 5. e2e 测试
cd e2e && npx playwright test && cd ..
```

全部通过 = Phase 1 完成。
