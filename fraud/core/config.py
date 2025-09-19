from functools import lru_cache
from typing import Optional

from pydantic import AnyUrl
from pydantic import Field
from pydantic import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
	model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True, extra="ignore")

	app_name: str = Field(default="Caravanes API")
	environment: str = Field(default="development")
	debug: bool = Field(default=True)

	database_url: Optional[str] = Field(default=None, alias="DATABASE_URL")

	# Gemini API
	gemini_api_key: Optional[str] = Field(default=None, alias="GEMINI_API_KEY")

	# CORS
	backend_cors_origins: list[str] = Field(default_factory=lambda: ["*"])

	# Vector DB
	vector_db_url: Optional[str] = Field(default="http://qdrant:6333", alias="VECTOR_DB_URL")

	# Kafka (external cluster defaults)
	kafka_bootstrap_servers: str = Field(default="10.103.44.199:19092", alias="KAFKA_BOOTSTRAP_SERVERS")
	kafka_rest_url: Optional[str] = Field(default="http://10.103.44.199:8080", alias="KAFKA_REST_URL")
	# Kafka topic
	kafka_topic: str = "plate_detect"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
	try:
		return Settings()  # type: ignore[call-arg]
	except ValidationError as exc:
		raise RuntimeError(f"Invalid environment configuration: {exc}")
