from fastapi import APIRouter
from app.api.routes.health import router as health_router

api_router = APIRouter()

# Mount health endpoints
api_router.include_router(health_router, prefix="/health", tags=["health"])
