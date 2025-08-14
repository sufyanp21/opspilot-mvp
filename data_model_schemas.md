# Derivatives Data Model Schemas

## Overview

This document defines the canonical data model for the derivatives data automation platform, inspired by industry standards (FIX, FpML, ISO 20022) and tailored for ETD and OTC derivatives workflows.

## Core Design Principles

1. **Immutability**: Core trade data is append-only with versioning
2. **Auditability**: Complete lineage tracking for all data modifications
3. **Flexibility**: Support for both ETD and OTC product types
4. **Compliance**: Built-in fields for regulatory reporting requirements
5. **Performance**: Optimized for reconciliation and querying patterns

## Base Entities

### 1. Trade Entity

The central entity representing any derivatives transaction.

```python
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field

class TradeStatus(str, Enum):
    NEW = "NEW"
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    AMENDED = "AMENDED"
    EXERCISED = "EXERCISED"
    EXPIRED = "EXPIRED"
    SETTLED = "SETTLED"

class TradeSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    PAY = "PAY"
    RECEIVE = "RECEIVE"

class ClearingStatus(str, Enum):
    UNCLEARED = "UNCLEARED"
    PENDING_CLEARING = "PENDING_CLEARING"
    CLEARED = "CLEARED"
    REJECTED = "REJECTED"

class Trade(BaseModel):
    # Primary Identifiers
    id: UUID = Field(..., description="Internal system ID")
    trade_id: str = Field(..., description="Internal trade ID")
    external_id: Optional[str] = Field(None, description="External system ID")
    
    # Regulatory Identifiers
    uti: Optional[str] = Field(None, description="Unique Transaction Identifier")
    upi: Optional[str] = Field(None, description="Unique Product Identifier")
    lei: Optional[str] = Field(None, description="Legal Entity Identifier")
    
    # CCP Identifiers
    ccp_trade_id: Optional[str] = Field(None, description="CCP assigned trade ID")
    clearing_house: Optional[str] = Field(None, description="Clearing house code")
    clearing_status: ClearingStatus = Field(ClearingStatus.UNCLEARED)
    
    # Trade Economics
    product_id: UUID = Field(..., description="Reference to Product entity")
    notional: Decimal = Field(..., description="Trade notional amount")
    price: Optional[Decimal] = Field(None, description="Trade price")
    quantity: Decimal = Field(..., description="Number of contracts/units")
    currency: str = Field(..., description="Primary currency (ISO 4217)")
    side: TradeSide = Field(..., description="Buy/Sell or Pay/Receive")
    
    # Parties
    counterparty_id: UUID = Field(..., description="Reference to Counterparty")
    portfolio_id: UUID = Field(..., description="Reference to Portfolio")
    account_id: str = Field(..., description="Trading account")
    trader_id: Optional[str] = Field(None, description="Trader identifier")
    broker_id: Optional[UUID] = Field(None, description="Executing broker")
    
    # Timestamps
    trade_date: date = Field(..., description="Trade execution date")
    trade_time: datetime = Field(..., description="Trade execution timestamp")
    value_date: date = Field(..., description="Settlement/value date")
    maturity_date: Optional[date] = Field(None, description="Maturity date")
    
    # Status and Lifecycle
    status: TradeStatus = Field(TradeStatus.NEW)
    version: int = Field(1, description="Trade version number")
    amended_from: Optional[UUID] = Field(None, description="Original trade if amended")
    
    # Market Data Context
    market_data_snapshot_id: Optional[UUID] = Field(None)
    
    # Audit Fields
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = Field(..., description="User/system that created the trade")
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    updated_by: str = Field(..., description="User/system that last updated")
    source_system: str = Field(..., description="Originating system")
    
    # Custom Fields for venue-specific data
    custom_fields: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        schema_extra = {
            "example": {
                "trade_id": "TRD-2024-001234",
                "uti": "1234567890ABCDEF1234567890ABCDEF12345678",
                "notional": "10000000.00",
                "quantity": "100",
                "currency": "USD",
                "side": "BUY",
                "trade_date": "2024-01-15",
                "value_date": "2024-01-17"
            }
        }
```

### 2. Product Entity

Represents financial instruments, supporting both ETD and OTC products.

```python
class ProductType(str, Enum):
    # ETD Products
    FUTURE = "FUTURE"
    OPTION = "OPTION"
    
    # OTC Products
    INTEREST_RATE_SWAP = "INTEREST_RATE_SWAP"
    FX_FORWARD = "FX_FORWARD"
    FX_SWAP = "FX_SWAP"
    CREDIT_DEFAULT_SWAP = "CREDIT_DEFAULT_SWAP"

class OptionType(str, Enum):
    CALL = "CALL"
    PUT = "PUT"

class DayCountConvention(str, Enum):
    ACT_360 = "ACT/360"
    ACT_365 = "ACT/365"
    THIRTY_360 = "30/360"
    ACT_ACT = "ACT/ACT"

class Product(BaseModel):
    # Identifiers
    id: UUID = Field(..., description="Internal product ID")
    symbol: Optional[str] = Field(None, description="Exchange symbol")
    isin: Optional[str] = Field(None, description="ISIN code")
    cusip: Optional[str] = Field(None, description="CUSIP code")
    ric: Optional[str] = Field(None, description="Reuters code")
    bloomberg_id: Optional[str] = Field(None, description="Bloomberg ID")
    
    # Basic Product Info
    product_type: ProductType = Field(...)
    name: str = Field(..., description="Product name")
    description: Optional[str] = Field(None)
    
    # ETD Specific Fields
    exchange: Optional[str] = Field(None, description="Exchange code")
    contract_month: Optional[str] = Field(None, description="Contract month (YYYYMM)")
    expiry_date: Optional[date] = Field(None, description="Expiry/maturity date")
    
    # Option Specific
    option_type: Optional[OptionType] = Field(None)
    strike_price: Optional[Decimal] = Field(None)
    
    # OTC Specific Fields
    underlying_asset: Optional[str] = Field(None)
    pay_frequency: Optional[str] = Field(None, description="Payment frequency")
    reset_frequency: Optional[str] = Field(None, description="Reset frequency")
    day_count_convention: Optional[DayCountConvention] = Field(None)
    
    # Currency Information
    base_currency: str = Field(..., description="Base currency")
    quote_currency: Optional[str] = Field(None, description="Quote currency for FX")
    
    # Contract Specifications
    contract_size: Optional[Decimal] = Field(None, description="Contract size/multiplier")
    tick_size: Optional[Decimal] = Field(None, description="Minimum price increment")
    tick_value: Optional[Decimal] = Field(None, description="Value per tick")
    
    # Regulatory
    asset_class: str = Field(..., description="Asset class for regulatory reporting")
    cfic: Optional[str] = Field(None, description="Classification of Financial Instruments Code")
    
    # Status
    is_active: bool = Field(True)
    
    # Audit
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        schema_extra = {
            "example": {
                "symbol": "ESH4",
                "product_type": "FUTURE",
                "name": "E-mini S&P 500 March 2024",
                "exchange": "CME",
                "contract_month": "202403",
                "base_currency": "USD",
                "contract_size": "50"
            }
        }
```

### 3. Position Entity

Aggregated view of holdings by account and instrument.

```python
class Position(BaseModel):
    # Identifiers
    id: UUID = Field(...)
    account_id: str = Field(...)
    product_id: UUID = Field(...)
    portfolio_id: UUID = Field(...)
    
    # Position Details
    quantity: Decimal = Field(..., description="Net position quantity")
    average_price: Optional[Decimal] = Field(None, description="Volume-weighted average price")
    market_value: Optional[Decimal] = Field(None, description="Current market value")
    unrealized_pnl: Optional[Decimal] = Field(None, description="Unrealized P&L")
    realized_pnl: Decimal = Field(Decimal('0'), description="Realized P&L")
    
    # Risk Metrics
    delta: Optional[Decimal] = Field(None, description="Price sensitivity")
    gamma: Optional[Decimal] = Field(None, description="Delta sensitivity")
    theta: Optional[Decimal] = Field(None, description="Time decay")
    vega: Optional[Decimal] = Field(None, description="Volatility sensitivity")
    
    # Margin Information
    initial_margin: Optional[Decimal] = Field(None)
    maintenance_margin: Optional[Decimal] = Field(None)
    variation_margin: Optional[Decimal] = Field(None)
    
    # Timestamps
    position_date: date = Field(..., description="Position as of date")
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    
    # Source and Reconciliation
    source_system: str = Field(...)
    is_reconciled: bool = Field(False)
    last_reconciled_at: Optional[datetime] = Field(None)
    
    class Config:
        schema_extra = {
            "example": {
                "account_id": "ACC-12345",
                "quantity": "150",
                "average_price": "4250.50",
                "position_date": "2024-01-15"
            }
        }
```

### 4. Cash Flow Entity

Represents cash movements and fees.

```python
class CashFlowType(str, Enum):
    PREMIUM = "PREMIUM"
    COMMISSION = "COMMISSION"
    EXCHANGE_FEE = "EXCHANGE_FEE"
    CLEARING_FEE = "CLEARING_FEE"
    REGULATORY_FEE = "REGULATORY_FEE"
    MARGIN_CALL = "MARGIN_CALL"
    MARGIN_RETURN = "MARGIN_RETURN"
    COUPON = "COUPON"
    SETTLEMENT = "SETTLEMENT"
    DIVIDEND = "DIVIDEND"
    INTEREST = "INTEREST"

class CashFlow(BaseModel):
    # Identifiers
    id: UUID = Field(...)
    trade_id: Optional[UUID] = Field(None, description="Related trade")
    account_id: str = Field(...)
    
    # Cash Flow Details
    flow_type: CashFlowType = Field(...)
    amount: Decimal = Field(..., description="Cash flow amount")
    currency: str = Field(..., description="Currency code")
    
    # Dates
    value_date: date = Field(..., description="Settlement date")
    booking_date: date = Field(..., description="Booking date")
    
    # Additional Context
    description: Optional[str] = Field(None)
    reference: Optional[str] = Field(None, description="External reference")
    counterparty_id: Optional[UUID] = Field(None)
    
    # Status
    is_settled: bool = Field(False)
    settled_at: Optional[datetime] = Field(None)
    
    # Audit
    created_at: datetime = Field(default_factory=datetime.utcnow)
    source_system: str = Field(...)
```

### 5. Lifecycle Event Entity

Captures trade lifecycle changes and corporate actions.

```python
class EventType(str, Enum):
    RATE_FIXING = "RATE_FIXING"
    PAYMENT_RESET = "PAYMENT_RESET"
    EXERCISE = "EXERCISE"
    ASSIGNMENT = "ASSIGNMENT"
    EXPIRY = "EXPIRY"
    EARLY_TERMINATION = "EARLY_TERMINATION"
    CORPORATE_ACTION = "CORPORATE_ACTION"
    AMENDMENT = "AMENDMENT"
    NOVATION = "NOVATION"
    COMPRESSION = "COMPRESSION"

class LifecycleEvent(BaseModel):
    # Identifiers
    id: UUID = Field(...)
    trade_id: UUID = Field(...)
    
    # Event Details
    event_type: EventType = Field(...)
    event_date: date = Field(...)
    effective_date: date = Field(...)
    
    # Event Data
    event_data: Dict[str, Any] = Field(default_factory=dict)
    
    # For Rate Fixings
    fixing_rate: Optional[Decimal] = Field(None)
    reference_rate: Optional[str] = Field(None)
    
    # For Exercises/Assignments
    exercise_quantity: Optional[Decimal] = Field(None)
    exercise_price: Optional[Decimal] = Field(None)
    
    # Processing Status
    is_processed: bool = Field(False)
    processed_at: Optional[datetime] = Field(None)
    
    # Audit
    created_at: datetime = Field(default_factory=datetime.utcnow)
    source_system: str = Field(...)
```

### 6. Counterparty Entity

Master data for trading counterparties.

```python
class CounterpartyType(str, Enum):
    BANK = "BANK"
    BROKER = "BROKER"
    HEDGE_FUND = "HEDGE_FUND"
    ASSET_MANAGER = "ASSET_MANAGER"
    CORPORATION = "CORPORATION"
    GOVERNMENT = "GOVERNMENT"
    CCP = "CCP"

class Counterparty(BaseModel):
    # Identifiers
    id: UUID = Field(...)
    name: str = Field(...)
    short_name: Optional[str] = Field(None)
    legal_name: str = Field(...)
    
    # Regulatory Identifiers
    lei: Optional[str] = Field(None, description="Legal Entity Identifier")
    bic: Optional[str] = Field(None, description="Bank Identifier Code")
    
    # Classification
    counterparty_type: CounterpartyType = Field(...)
    sector: Optional[str] = Field(None)
    country: str = Field(..., description="Country of domicile")
    
    # Credit Information
    credit_rating: Optional[str] = Field(None)
    credit_limit: Optional[Decimal] = Field(None)
    
    # Contact Information
    address: Optional[Dict[str, str]] = Field(None)
    contact_email: Optional[str] = Field(None)
    contact_phone: Optional[str] = Field(None)
    
    # Status
    is_active: bool = Field(True)
    approved_products: List[str] = Field(default_factory=list)
    
    # Audit
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

### 7. Margin Entity

Margin and collateral management.

```python
class MarginType(str, Enum):
    INITIAL = "INITIAL"
    VARIATION = "VARIATION"
    ADDITIONAL = "ADDITIONAL"

class CollateralType(str, Enum):
    CASH = "CASH"
    GOVERNMENT_BOND = "GOVERNMENT_BOND"
    CORPORATE_BOND = "CORPORATE_BOND"
    EQUITY = "EQUITY"
    LETTER_OF_CREDIT = "LETTER_OF_CREDIT"

class Margin(BaseModel):
    # Identifiers
    id: UUID = Field(...)
    account_id: str = Field(...)
    ccp: Optional[str] = Field(None)
    
    # Margin Details
    margin_type: MarginType = Field(...)
    currency: str = Field(...)
    required_amount: Decimal = Field(...)
    posted_amount: Decimal = Field(...)
    
    # Calculation Details
    calculation_date: date = Field(...)
    calculation_method: Optional[str] = Field(None)
    portfolio_id: Optional[UUID] = Field(None)
    
    # Collateral
    collateral_type: CollateralType = Field(...)
    collateral_value: Decimal = Field(...)
    haircut: Optional[Decimal] = Field(None)
    
    # Call Information
    margin_call_amount: Optional[Decimal] = Field(None)
    call_due_date: Optional[date] = Field(None)
    is_call_satisfied: bool = Field(True)
    
    # Audit
    created_at: datetime = Field(default_factory=datetime.utcnow)
    source_system: str = Field(...)
```

## Reconciliation-Specific Entities

### 8. Reconciliation Run

```python
class ReconStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class ReconciliationRun(BaseModel):
    # Identifiers
    id: UUID = Field(...)
    name: str = Field(...)
    run_date: date = Field(...)
    
    # Configuration
    recon_config_id: UUID = Field(...)
    source_systems: List[str] = Field(...)
    
    # Status and Timing
    status: ReconStatus = Field(ReconStatus.PENDING)
    started_at: Optional[datetime] = Field(None)
    completed_at: Optional[datetime] = Field(None)
    
    # Results Summary
    total_records: int = Field(0)
    matched_records: int = Field(0)
    unmatched_records: int = Field(0)
    break_count: int = Field(0)
    
    # Statistics
    match_rate: Optional[Decimal] = Field(None)
    processing_time_seconds: Optional[int] = Field(None)
    
    # Metadata
    triggered_by: str = Field(...)
    run_parameters: Dict[str, Any] = Field(default_factory=dict)
    
    # Audit
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

### 9. Break (Exception)

```python
class BreakSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class BreakStatus(str, Enum):
    OPEN = "OPEN"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CANCELLED = "CANCELLED"
    ESCALATED = "ESCALATED"

class Break(BaseModel):
    # Identifiers
    id: UUID = Field(...)
    recon_run_id: UUID = Field(...)
    break_reference: str = Field(..., description="Human-readable reference")
    
    # Break Details
    break_type: str = Field(..., description="Type of break")
    severity: BreakSeverity = Field(...)
    status: BreakStatus = Field(BreakStatus.OPEN)
    
    # Data Context
    source_record_id: Optional[str] = Field(None)
    target_record_id: Optional[str] = Field(None)
    field_differences: Dict[str, Any] = Field(default_factory=dict)
    
    # Assignment
    assigned_to: Optional[str] = Field(None)
    assigned_at: Optional[datetime] = Field(None)
    team: Optional[str] = Field(None)
    
    # Resolution
    resolution_type: Optional[str] = Field(None)
    resolution_comment: Optional[str] = Field(None)
    resolved_by: Optional[str] = Field(None)
    resolved_at: Optional[datetime] = Field(None)
    
    # SLA Tracking
    sla_due_date: Optional[datetime] = Field(None)
    is_sla_breached: bool = Field(False)
    
    # Root Cause Analysis
    probable_cause: Optional[str] = Field(None)
    root_cause: Optional[str] = Field(None)
    
    # Audit
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

## Audit and Governance Entities

### 10. Audit Trail

```python
class AuditAction(str, Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    VIEW = "VIEW"
    EXPORT = "EXPORT"
    APPROVE = "APPROVE"
    REJECT = "REJECT"

class AuditTrail(BaseModel):
    # Identifiers
    id: UUID = Field(...)
    correlation_id: str = Field(..., description="Request correlation ID")
    
    # Action Details
    action: AuditAction = Field(...)
    entity_type: str = Field(..., description="Type of entity modified")
    entity_id: str = Field(..., description="ID of entity modified")
    
    # User Context
    user_id: str = Field(...)
    username: str = Field(...)
    user_ip: Optional[str] = Field(None)
    user_agent: Optional[str] = Field(None)
    
    # Change Details
    old_values: Optional[Dict[str, Any]] = Field(None)
    new_values: Optional[Dict[str, Any]] = Field(None)
    
    # Context
    reason: Optional[str] = Field(None)
    system_context: Dict[str, Any] = Field(default_factory=dict)
    
    # Timestamp
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        # Immutable audit records
        allow_mutation = False
```

## Key Design Features

### 1. Flexible Product Model
- Supports both ETD and OTC products in single schema
- Extensible for new product types
- Rich metadata for various identifier systems

### 2. Comprehensive Trade Lifecycle
- Version control for trade amendments
- Complete audit trail
- Support for complex lifecycle events

### 3. Multi-Source Reconciliation
- Clear data lineage tracking
- Configurable tolerance handling
- Break clustering and root cause analysis

### 4. Regulatory Compliance
- Built-in fields for major regulations (EMIR, CFTC, MiFIR)
- UTI/UPI tracking
- Complete audit trail

### 5. Performance Optimization
- Indexed fields for common query patterns
- Denormalized views for reporting
- Efficient data structures for reconciliation

### 6. Data Quality
- Strong typing with validation
- Immutable audit records
- Comprehensive error tracking

This data model provides the foundation for a robust, scalable, and compliant derivatives data automation platform that can handle the complexity of modern derivatives workflows while maintaining data integrity and regulatory compliance.
