from sqlalchemy import Column, String, Numeric, Date, DateTime, Integer, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, date
import enum
from decimal import Decimal

from app.models.base import BaseModel

class TradeSide(str, enum.Enum):
    BUY = "BUY"
    SELL = "SELL"

class TradeInternal(BaseModel):
    """Model for internal trade data."""
    __tablename__ = "trades_internal"
    
    # Core identifiers
    trade_id = Column(String(100), nullable=False, index=True)
    account = Column(String(100), nullable=False, index=True)
    symbol = Column(String(50), nullable=False, index=True)
    
    # Trade details
    side = Column(SQLEnum(TradeSide), nullable=False)
    qty = Column(Integer, nullable=False)
    price = Column(Numeric(15, 6), nullable=False)
    
    # Dates
    trade_date = Column(Date, nullable=False, index=True)
    
    # Additional fields
    exchange = Column(String(50), nullable=True)
    clearing_ref = Column(String(100), nullable=True)
    
    # Source information
    source_file_id = Column(UUID(as_uuid=True), nullable=True)
    row_number = Column(Integer, nullable=True)  # Row in source file
    
    # Raw data (JSON stored as text)
    raw_data = Column(Text, nullable=True)

class TradeCleared(BaseModel):
    """Model for cleared trade data."""
    __tablename__ = "trades_cleared"
    
    # Core identifiers (same structure as internal for reconciliation)
    trade_id = Column(String(100), nullable=False, index=True)
    account = Column(String(100), nullable=False, index=True)
    symbol = Column(String(50), nullable=False, index=True)
    
    # Trade details
    side = Column(SQLEnum(TradeSide), nullable=False)
    qty = Column(Integer, nullable=False)
    price = Column(Numeric(15, 6), nullable=False)
    
    # Dates
    trade_date = Column(Date, nullable=False, index=True)
    
    # Additional fields
    exchange = Column(String(50), nullable=True)
    clearing_ref = Column(String(100), nullable=True)
    
    # Source information
    source_file_id = Column(UUID(as_uuid=True), nullable=True)
    row_number = Column(Integer, nullable=True)  # Row in source file
    
    # Raw data (JSON stored as text)
    raw_data = Column(Text, nullable=True)
