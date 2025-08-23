from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class AuditLog(Base):
    __tablename__ = "audit_log"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ts_utc: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    user_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    actor_email: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    object_type: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    object_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    details: Mapped[Any] = mapped_column(JSON, nullable=True)


class BreakStatusEnum(str, Enum):  # type: ignore[misc]
    NEW = "NEW"
    ASSIGNED = "ASSIGNED"
    RESOLVED = "RESOLVED"
    SUPPRESSED = "SUPPRESSED"
    ESCALATED = "ESCALATED"


class BreakTypeEnum(str, Enum):  # type: ignore[misc]
    MISSING_INT = "MISSING_INT"
    MISSING_EXT = "MISSING_EXT"
    FIELD_MISMATCH = "FIELD_MISMATCH"
    TIMING = "TIMING"


class BreakSeverityEnum(str, Enum):  # type: ignore[misc]
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Break(Base):
    __tablename__ = "breaks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(16), nullable=False)
    assigned_to: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    reason_code: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    notes: Mapped[Any] = mapped_column(JSON, nullable=True)
    lineage: Mapped[Any] = mapped_column(JSON, nullable=True)  # {internal_ids:[], external_ids:[]}

    comments = relationship("BreakComment", back_populates="break_ref", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_breaks_run_status", "run_id", "status"),
        Index("ix_breaks_run_type", "run_id", "type"),
    )


class BreakComment(Base):
    __tablename__ = "break_comments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    break_id: Mapped[int] = mapped_column(ForeignKey("breaks.id", ondelete="CASCADE"))
    user_id: Mapped[str] = mapped_column(String(64), nullable=False)
    ts_utc: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    text: Mapped[str] = mapped_column(String(2000), nullable=False)

    break_ref = relationship("Break", back_populates="comments")


class FileRegistry(Base):
    __tablename__ = "file_registry"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    size: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    received_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="received")
    error: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)


class ReconRun(Base):
    __tablename__ = "recon_runs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    source_set: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    matched: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    auto_tol: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    breaks_by_type: Mapped[Any] = mapped_column(JSON, nullable=True)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="completed")
    error: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)



class MappingTemplate(Base):
    __tablename__ = "mapping_templates"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    mapping_json: Mapped[Any] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class MLModel(Base):
    __tablename__ = "ml_models"
    model_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    kind: Mapped[str] = mapped_column(String(64), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    trained_from: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    run_window: Mapped[Any] = mapped_column(JSON, nullable=True)
    metrics: Mapped[Any] = mapped_column(JSON, nullable=True)
    features: Mapped[Any] = mapped_column(JSON, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)


class PredictionBreak(Base):
    __tablename__ = "predictions_breaks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    record_id: Mapped[str] = mapped_column(String(128), nullable=False)
    model_id: Mapped[str] = mapped_column(String(64), nullable=False)
    model_type: Mapped[str] = mapped_column(String(32), nullable=False, default="ml")
    p_break: Mapped[float] = mapped_column(Integer, nullable=False, default=0)  # store as 0-100 basis points for SQLite simplicity
    p_type: Mapped[Any] = mapped_column(JSON, nullable=True)
    ttfr_bucket: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    autoclear_suggest: Mapped[Optional[bool]] = mapped_column(Integer, nullable=True)
    explanation_top: Mapped[Any] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    __table_args__ = (
        Index("ix_predictions_breaks_run_model_record", "run_id", "model_id", "record_id", unique=True),
    )


class AnomalyLog(Base):
    __tablename__ = "anomalies_log"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ts_utc: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    metric: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    value: Mapped[Any] = mapped_column(JSON, nullable=False)
    threshold: Mapped[Any] = mapped_column(JSON, nullable=False)
    anomaly_type: Mapped[str] = mapped_column(String(64), nullable=False)
    run_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)


