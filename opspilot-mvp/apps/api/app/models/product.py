"""Product model with tick size and contract specifications."""

from sqlalchemy import Column, String, Numeric, Integer, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.models.base import BaseModel
from app.core.enums import ProductType


class Product(BaseModel):
    """Product master data with tick specifications."""
    
    __tablename__ = "products"
    
    # Core identifiers
    symbol = Column(String, nullable=False, unique=True, index=True)
    product_type = Column(String, nullable=False, default=ProductType.ETD)
    exchange = Column(String, nullable=False, index=True)
    
    # Product specifications
    name = Column(String, nullable=True)
    description = Column(String, nullable=True)
    
    # Tick specifications (critical for ETD reconciliation)
    tick_size = Column(Numeric(10, 6), nullable=False, default=0.25)
    tick_value = Column(Numeric(15, 2), nullable=True)  # Dollar value per tick
    contract_size = Column(Integer, nullable=True, default=1)
    
    # Trading specifications
    is_active = Column(Boolean, nullable=False, default=True)
    currency = Column(String(3), nullable=False, default="USD")
    
    # Metadata
    sector = Column(String, nullable=True)
    asset_class = Column(String, nullable=True)
    
    # Indexes for performance
    __table_args__ = (
        Index('ix_products_symbol_exchange', 'symbol', 'exchange'),
        Index('ix_products_type_active', 'product_type', 'is_active'),
    )
    
    def __repr__(self):
        return f"<Product(symbol='{self.symbol}', exchange='{self.exchange}', tick_size={self.tick_size})>"
    
    @property
    def full_symbol(self) -> str:
        """Return exchange-qualified symbol."""
        return f"{self.symbol}@{self.exchange}"
    
    def price_to_ticks(self, price: float) -> float:
        """Convert price to number of ticks."""
        return float(price) / float(self.tick_size)
    
    def ticks_to_price(self, ticks: float) -> float:
        """Convert ticks to price."""
        return float(ticks) * float(self.tick_size)
    
    def round_to_tick(self, price: float) -> float:
        """Round price to nearest valid tick."""
        ticks = round(self.price_to_ticks(price))
        return self.ticks_to_price(ticks)
