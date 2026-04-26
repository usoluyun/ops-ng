from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from middleware.auth import AuthMiddleware
from routers import hotels, rooms, users

app = FastAPI(
    title="ops-ng BBF Gateway",
    description="Backend for Frontend - API Gateway for ops-ng",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(AuthMiddleware)

app.include_router(hotels.router, prefix="/api")
app.include_router(rooms.router, prefix="/api")
app.include_router(users.router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok"}
