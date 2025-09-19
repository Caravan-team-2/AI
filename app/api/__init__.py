from fastapi import APIRouter
from app.api.routes.health import router as health_router
from app.api.routes.ocr import router as ocr_router
from app.api.routes.damage_estimation import router as damage_router


api_router = APIRouter()

# Mount health endpoints
api_router.include_router(health_router, prefix="/health", tags=["health"])
api_router.include_router(ocr_router, prefix="/ocr", tags=["ocr"])
api_router.include_router(damage_router, prefix="/damage", tags=["damage-estimation"])
