from __future__ import annotations

from datetime import date
from typing import Optional, List

from pydantic import BaseModel, Field


class OTCTrade(BaseModel):
    uti: Optional[str] = Field(None)
    trade_date: Optional[date] = None
    counterparty: Optional[str] = None
    notional: float
    ccy: str
    product: str
    fixed_rate: Optional[float] = None
    float_idx: Optional[str] = None
    maturity: Optional[date] = None
    legs: Optional[List[dict]] = None


