from __future__ import annotations

import os
from datetime import datetime
from typing import Generator, Optional

from sqlalchemy import create_engine, String, DateTime, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker, Session


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./opspilot.db")


class Base(DeclarativeBase):
    pass


class AuditHeader(Base):
    __tablename__ = "audit_headers"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    correlation_id: Mapped[str | None] = mapped_column(String(64), nullable=True)


engine = create_engine(DATABASE_URL) if DATABASE_URL else None
SessionLocal = sessionmaker(bind=engine) if engine else None


def init_db() -> None:
    if engine:
        # Migration-safe in MVP: ensure tables exist
        Base.metadata.create_all(bind=engine)


def get_session() -> Generator[Session, None, None]:
    if not SessionLocal:
        raise RuntimeError("Database not configured")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_session_optional() -> Generator[Optional[Session], None, None]:
    if not SessionLocal:
        yield None
        return
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


