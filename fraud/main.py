from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fraud.kafka.consumer import consumer
from fraud.core.config import get_settings


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


	@application.on_event("startup")
	async def _start_consumer() -> None:
		consumer.start()

	@application.on_event("shutdown")
	async def _stop_consumer() -> None:
		consumer.stop()
	return application


app = create_application()
