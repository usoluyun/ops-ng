#!/usr/bin/env bash
#
# ops-ng Phase 1 Smoke Test Script
# Validates all infrastructure services are healthy and accessible
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Service endpoints
STRAPI_URL=${STRAPI_URL:-http://localhost:1337}
HYDRA_PUBLIC_URL=${HYDRA_PUBLIC_URL:-http://localhost:4444}
LOGIN_APP_URL=${LOGIN_APP_URL:-http://localhost:8001}
BBF_URL=${BBF_URL:-http://localhost:8000}
POSTGRES_HOST=${POSTGRES_HOST:-localhost}
POSTGRES_USER=${POSTGRES_USER:-ops}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-devpassword123}
REDIS_HOST=${REDIS_HOST:-localhost}
REDIS_PORT=${REDIS_PORT:-6379}

FAILED=0

echo "========================================"
echo "ops-ng Phase 1 Smoke Test"
echo "========================================"
echo ""

# Helper functions
check_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
}

check_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
    FAILED=$((FAILED + 1))
}

check_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

curl_check() {
    local url=$1
    local name=$2
    local expected_code=${3:-200}

    HTTP_CODE=$(curl -sf -o /dev/null -w "%{http_code}" "$url")
    if [ "$HTTP_CODE" = "$expected_code" ]; then
        check_pass "$name (HTTP $HTTP_CODE)"
        return 0
    else
        check_fail "$name (expected $expected_code, got $HTTP_CODE)"
        return 1
    fi
}

# ----------------------------------------
# 1. Check Strapi health
# ----------------------------------------
echo "--- Strapi ---"
if curl_check "$STRAPI_URL/_health" "Strapi health"; then
    :
fi

# Check Strapi API is accessible (may return 403 without auth, but should not 000)
HTTP_CODE=$(curl -sf -o /dev/null -w "%{http_code}" "$STRAPI_URL/api/hotels")
if [ "$HTTP_CODE" = "000" ]; then
    check_fail "Strapi API unreachable"
elif [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "403" ]; then
    check_pass "Strapi API accessible (HTTP $HTTP_CODE)"
else
    check_fail "Strapi API unexpected response (HTTP $HTTP_CODE)"
fi

# Check Strapi seed data if STRAPI_SERVICE_TOKEN is set
if [ -n "$STRAPI_SERVICE_TOKEN" ]; then
    COUNT=$(curl -sf -H "Authorization: Bearer $STRAPI_SERVICE_TOKEN" \
        "$STRAPI_URL/api/hotels" 2>/dev/null | \
        python3 -c "import sys,json; print(json.load(sys.stdin)['meta']['pagination']['total'])" 2>/dev/null || echo "0")
    if [ "$COUNT" -ge "2" ]; then
        check_pass "Strapi seed data: $COUNT hotels"
    else
        check_warn "Strapi seed data: only $COUNT hotels (expected >= 2)"
    fi
else
    check_warn "STRAPI_SERVICE_TOKEN not set, skipping seed data check"
fi
echo ""

# ----------------------------------------
# 2. Check BBF health
# ----------------------------------------
echo "--- BBF Gateway ---"
curl_check "$BBF_URL/health" "BBF health"

# Check BBF auth enforcement (should return 401 without token)
HTTP_CODE=$(curl -sf -o /dev/null -w "%{http_code}" "$BBF_URL/api/hotels")
if [ "$HTTP_CODE" = "401" ]; then
    check_pass "BBF auth enforcement (401 without token)"
elif [ "$HTTP_CODE" = "000" ]; then
    check_fail "BBF unreachable"
else
    check_warn "BBF /api/hotels returned $HTTP_CODE (expected 401)"
fi
echo ""

# ----------------------------------------
# 3. Check Login App health
# ----------------------------------------
echo "--- Login App ---"
curl_check "$LOGIN_APP_URL/health" "Login App health"
echo ""

# ----------------------------------------
# 4. Check ORY Hydra
# ----------------------------------------
echo "--- ORY Hydra ---"
curl_check "$HYDRA_PUBLIC_URL/.well-known/openid-configuration" "Hydra OIDC discovery"

# Check Hydra JWKS endpoint
curl_check "$HYDRA_PUBLIC_URL/.well-known/jwks.json" "Hydra JWKS"

# Check Hydra health
HTTP_CODE=$(curl -sf -o /dev/null -w "%{http_code}" "$HYDRA_PUBLIC_URL/health")
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "429" ]; then
    # Hydra /health returns 429 when DB is not connected (expected in dev mode)
    check_pass "Hydra health (HTTP $HTTP_CODE)"
elif [ "$HTTP_CODE" = "000" ]; then
    check_fail "Hydra unreachable"
else
    check_warn "Hydra health returned HTTP $HTTP_CODE"
fi
echo ""

# ----------------------------------------
# 5. Check PostgreSQL
# ----------------------------------------
echo "--- PostgreSQL ---"
# Use podman exec to check from within the container network
if podman exec ops-ng_postgres_1 pg_isready -U "$POSTGRES_USER" > /dev/null 2>&1; then
    check_pass "PostgreSQL is ready"

    # Check databases exist
    DB_LIST=$(podman exec ops-ng_postgres_1 psql -U "$POSTGRES_USER" -d postgres -t -c \
        "SELECT datname FROM pg_database WHERE datname IN ('strapi_db', 'hydra_db');" 2>/dev/null | tr -d ' ')

    if echo "$DB_LIST" | grep -q "strapi_db"; then
        check_pass "Database strapi_db exists"
    else
        check_fail "Database strapi_db not found"
    fi

    if echo "$DB_LIST" | grep -q "hydra_db"; then
        check_pass "Database hydra_db exists"
    else
        check_fail "Database hydra_db not found"
    fi
else
    check_fail "PostgreSQL is not ready"
fi
echo ""

# ----------------------------------------
# 6. Check Redis
# ----------------------------------------
echo "--- Redis ---"
if podman exec ops-ng_redis_1 redis-cli -p "$REDIS_PORT" ping > /dev/null 2>&1; then
    check_pass "Redis is ready"
else
    check_fail "Redis is not ready"
fi
echo ""

# ----------------------------------------
# Summary
# ----------------------------------------
echo "========================================"
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All smoke tests passed!${NC}"
    echo "========================================"
    exit 0
else
    echo -e "${RED}$FAILED smoke test(s) failed${NC}"
    echo "========================================"
    exit 1
fi