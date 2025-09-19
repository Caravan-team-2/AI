from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ai.api import api_router
from ai.core.config import get_settings


def create_application() -> FastAPI:
	settings = get_settings()
	application = FastAPI(title=settings.app_name, version="0.1.0", debug=settings.debug)
	application.add_middleware(
		CORSMiddleware,
		allow_origins=settings.backend_cors_origins,
		allow_credentials=True,
		allow_methods=["*"],
		allow_headers=["*"],
	)
	application.include_router(api_router)
	return application


app = create_application()
