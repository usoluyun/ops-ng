#!/usr/bin/env bash
# verify-hydra.sh - Hydra 服务健康检查脚本
set -e

HYDRA_PUBLIC=${HYDRA_PUBLIC_URL:-http://localhost:4444}
HYDRA_ADMIN=${HYDRA_ADMIN_URL:-http://localhost:4445}

echo "=== Hydra 健康检查 ==="

echo "检查 Hydra public 端点..."
curl -sf "$HYDRA_PUBLIC/.well-known/openid-configuration" > /dev/null
echo "  OK: OIDC discovery"

echo "检查 Hydra admin API..."
curl -sf "$HYDRA_ADMIN/admin/clients" > /dev/null
echo "  OK: Admin API"

echo ""
echo "=== Hydra 健康检查通过 ==="
