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
