from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session

from ai.core.config import get_settings


settings = get_settings()
engine = create_engine(settings.database_url or "sqlite:///./data.db", future=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False, class_=Session)


def get_db() -> Iterator[Session]:
	db = SessionLocal()
	try:
		yield db
	finally:
		db.close()
