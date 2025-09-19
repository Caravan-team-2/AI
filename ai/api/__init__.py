from fastapi import APIRouter
from ai.api.routes.health import router as health_router
from ai.api.routes.ocr import router as ocr_router
from ai.api.routes.damage_estimation import router as damage_router
from ai.api.routes.license_plate import router as license_plate_router


api_router = APIRouter()

# Mount health endpoints
api_router.include_router(health_router, prefix="/health", tags=["health"])
api_router.include_router(ocr_router, prefix="/ocr", tags=["ocr"])
api_router.include_router(damage_router, prefix="/damage", tags=["damage-estimation"])
api_router.include_router(license_plate_router, prefix="/license-plate", tags=["license-plate"])
