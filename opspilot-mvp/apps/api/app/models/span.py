from sqlalchemy import Column, String, Numeric, Date, Integer
from sqlalchemy.dialects.postgresql import UUID
from datetime import date
from decimal import Decimal

from app.models.base import BaseModel

class SpanSnapshot(BaseModel):
    """Model for SPAN margin snapshots."""
    __tablename__ = "span_snapshots"
    
    # Date and identifiers
    asof_date = Column(Date, nullable=False, index=True)
    product = Column(String(50), nullable=False, index=True)
    account = Column(String(100), nullable=False, index=True)
    
    # Margin data
    scan_margin = Column(Numeric(15, 2), nullable=False)
    
    # Source information
    file_id = Column(UUID(as_uuid=True), nullable=False)
    row_number = Column(Integer, nullable=True)

class SpanDelta(BaseModel):
    """Model for SPAN margin deltas between snapshots."""
    __tablename__ = "span_deltas"
    
    # Date and identifiers
    asof_date = Column(Date, nullable=False, index=True)
    product = Column(String(50), nullable=False, index=True)
    account = Column(String(100), nullable=False, index=True)
    
    # Delta calculation
    scan_before = Column(Numeric(15, 2), nullable=True)
    scan_after = Column(Numeric(15, 2), nullable=False)
    delta = Column(Numeric(15, 2), nullable=False)
    
    # Source snapshots
    previous_snapshot_id = Column(UUID(as_uuid=True), nullable=True)
    current_snapshot_id = Column(UUID(as_uuid=True), nullable=False)
