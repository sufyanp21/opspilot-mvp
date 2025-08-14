"""Core enumerations for the application."""

from enum import Enum


class PriceToleranceMode(str, Enum):
    """Price tolerance calculation modes."""
    ABSOLUTE = "ABSOLUTE"
    PCT = "PCT"
    TICKS = "TICKS"


class ToleranceResult(str, Enum):
    """Result of tolerance checking."""
    MATCH = "MATCH"
    BREAK = "BREAK"


class ProductType(str, Enum):
    """Product type classifications."""
    ETD = "ETD"  # Exchange Traded Derivatives
    OTC = "OTC"  # Over The Counter
    CASH = "CASH"  # Cash instruments
