from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class Trade(BaseModel):
    # ISDA CDM correlates (pragmatic subset)
    # - tradeIdentifier → `trade_id`
    # - party → `party_internal`, `party_external`
    # - product/contract → `product_code`
    # - quantity → `quantity`
    # - price → `price`
    # - account → `account`
    # - execution timestamp → `execution_ts`
    trade_id: str = Field(..., description="Unique trade identifier (CDM: tradeIdentifier)")
    uti: Optional[str] = Field(None, description="Unique Transaction Identifier")
    upi: Optional[str] = Field(None, description="Unique Product Identifier")
    product_code: str = Field(..., description="Product/symbol (CDM: product)")
    account: Optional[str] = Field(None, description="Account identifier (CDM: account)")
    quantity: float = Field(..., description="Quantity (CDM: quantity)")
    price: float = Field(..., description="Price (CDM: price)")
    party_internal: Optional[str] = Field(None, description="Internal party (CDM: party)")
    party_external: Optional[str] = Field(None, description="External party (CDM: party)")
    execution_ts: Optional[datetime] = Field(None, description="Execution timestamp (CDM: tradeDate/time)")


class Position(BaseModel):
    # CDM position correlates: positionState/quantity/product
    product_code: str
    account: Optional[str]
    net_quantity: float


class LifecycleEvent(BaseModel):
    # CDM event correlates: eventType, eventDate, eventEffect
    event_type: str
    event_time: datetime
    trade_id: Optional[str]
    details: Optional[dict]


