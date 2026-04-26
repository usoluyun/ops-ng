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
