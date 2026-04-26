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
