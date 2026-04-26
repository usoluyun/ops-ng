#!/usr/bin/env bash
set -e

HYDRA_ADMIN=${HYDRA_ADMIN_URL:-http://localhost:4445}

echo "Registering OAuth2 client 'ops-ng-ui' with Hydra admin at $HYDRA_ADMIN..."

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

echo ""
echo "OAuth2 client 'ops-ng-ui' registration complete."