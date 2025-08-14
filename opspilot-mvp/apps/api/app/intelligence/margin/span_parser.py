"""SPAN file parser with detailed margin component extraction."""

import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from decimal import Decimal
from datetime import date, datetime
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class MarginComponents:
    """Detailed margin components for a position."""
    account: str
    product: str
    series: str  # Contract series (e.g., ESZ5, CLF6)
    as_of_date: date
    
    # Core SPAN components
    scan_risk: Decimal
    inter_spread_charge: Decimal
    short_opt_minimum: Decimal
    long_opt_credit: Decimal
    net_premium: Decimal
    add_on_margin: Decimal
    
    # Derived totals
    total_margin: Decimal
    net_position: int  # Net contracts (long - short)
    
    # Additional metadata
    underlying_price: Optional[Decimal] = None
    volatility_factor: Optional[Decimal] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "account": self.account,
            "product": self.product,
            "series": self.series,
            "as_of_date": self.as_of_date.isoformat(),
            "scan_risk": float(self.scan_risk),
            "inter_spread_charge": float(self.inter_spread_charge),
            "short_opt_minimum": float(self.short_opt_minimum),
            "long_opt_credit": float(self.long_opt_credit),
            "net_premium": float(self.net_premium),
            "add_on_margin": float(self.add_on_margin),
            "total_margin": float(self.total_margin),
            "net_position": self.net_position,
            "underlying_price": float(self.underlying_price) if self.underlying_price else None,
            "volatility_factor": float(self.volatility_factor) if self.volatility_factor else None
        }


class SPANParser:
    """Enhanced SPAN file parser with detailed component extraction."""
    
    def __init__(self):
        self.column_mappings = {
            # Standard SPAN column mappings
            "account": ["account", "account_id", "acct", "customer"],
            "product": ["product", "symbol", "underlying", "commodity"],
            "series": ["series", "contract", "expiry", "maturity"],
            "scan_risk": ["scan_risk", "scan", "initial_margin", "im"],
            "inter_spread_charge": ["inter_spread_charge", "inter_spread", "isc"],
            "short_opt_minimum": ["short_opt_minimum", "short_option_min", "som"],
            "long_opt_credit": ["long_opt_credit", "long_option_credit", "loc"],
            "net_premium": ["net_premium", "premium", "net_prem"],
            "add_on_margin": ["add_on_margin", "addon", "additional_margin"],
            "total_margin": ["total_margin", "total", "requirement"],
            "net_position": ["net_position", "position", "qty", "contracts"],
            "underlying_price": ["underlying_price", "price", "settlement"],
            "volatility_factor": ["volatility_factor", "vol_factor", "volatility"]
        }
    
    def parse_span_file(self, file_path: str, as_of_date: Optional[date] = None) -> List[MarginComponents]:
        """
        Parse SPAN CSV file into detailed margin components.
        
        Args:
            file_path: Path to SPAN CSV file
            as_of_date: Date for the SPAN data (extracted from filename if not provided)
            
        Returns:
            List of MarginComponents objects
        """
        logger.info(f"Parsing SPAN file: {file_path}")
        
        try:
            # Read CSV file
            df = pd.read_csv(file_path)
            logger.info(f"Loaded {len(df)} rows from SPAN file")
            
            # Extract date if not provided
            if as_of_date is None:
                as_of_date = self._extract_date_from_filename(file_path)
            
            # Normalize column names
            df = self._normalize_columns(df)
            
            # Validate required columns
            self._validate_required_columns(df)
            
            # Parse rows into margin components
            components = []
            for _, row in df.iterrows():
                try:
                    component = self._parse_row(row, as_of_date)
                    if component:
                        components.append(component)
                except Exception as e:
                    logger.warning(f"Failed to parse row: {e}")
                    continue
            
            logger.info(f"Successfully parsed {len(components)} margin components")
            return components
            
        except Exception as e:
            logger.error(f"Failed to parse SPAN file {file_path}: {e}")
            raise
    
    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize column names to standard format."""
        column_map = {}
        
        for standard_name, possible_names in self.column_mappings.items():
            for col in df.columns:
                col_lower = col.lower().strip()
                if col_lower in [name.lower() for name in possible_names]:
                    column_map[col] = standard_name
                    break
        
        df_normalized = df.rename(columns=column_map)
        
        # Log column mapping
        logger.debug(f"Column mapping applied: {column_map}")
        
        return df_normalized
    
    def _validate_required_columns(self, df: pd.DataFrame):
        """Validate that required columns are present."""
        required_columns = ["account", "product", "scan_risk", "total_margin"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
    
    def _parse_row(self, row: pd.Series, as_of_date: date) -> Optional[MarginComponents]:
        """Parse a single row into MarginComponents."""
        try:
            # Extract core fields
            account = str(row.get("account", "")).strip()
            product = str(row.get("product", "")).strip()
            series = str(row.get("series", product)).strip()  # Default to product if no series
            
            if not account or not product:
                return None
            
            # Parse margin components with defaults
            scan_risk = self._safe_decimal(row.get("scan_risk", 0))
            inter_spread_charge = self._safe_decimal(row.get("inter_spread_charge", 0))
            short_opt_minimum = self._safe_decimal(row.get("short_opt_minimum", 0))
            long_opt_credit = self._safe_decimal(row.get("long_opt_credit", 0))
            net_premium = self._safe_decimal(row.get("net_premium", 0))
            add_on_margin = self._safe_decimal(row.get("add_on_margin", 0))
            total_margin = self._safe_decimal(row.get("total_margin", 0))
            
            # Parse position and price data
            net_position = int(row.get("net_position", 0))
            underlying_price = self._safe_decimal(row.get("underlying_price"))
            volatility_factor = self._safe_decimal(row.get("volatility_factor"))
            
            # Create margin components object
            return MarginComponents(
                account=account,
                product=product,
                series=series,
                as_of_date=as_of_date,
                scan_risk=scan_risk,
                inter_spread_charge=inter_spread_charge,
                short_opt_minimum=short_opt_minimum,
                long_opt_credit=long_opt_credit,
                net_premium=net_premium,
                add_on_margin=add_on_margin,
                total_margin=total_margin,
                net_position=net_position,
                underlying_price=underlying_price,
                volatility_factor=volatility_factor
            )
            
        except Exception as e:
            logger.error(f"Error parsing row: {e}")
            return None
    
    def _safe_decimal(self, value: Any) -> Optional[Decimal]:
        """Safely convert value to Decimal."""
        if value is None or pd.isna(value):
            return None
        
        try:
            return Decimal(str(value))
        except:
            return None
    
    def _extract_date_from_filename(self, file_path: str) -> date:
        """Extract date from SPAN filename."""
        import re
        from pathlib import Path
        
        filename = Path(file_path).name
        
        # Try various date patterns
        patterns = [
            r'(\d{4}-\d{2}-\d{2})',  # YYYY-MM-DD
            r'(\d{4}\d{2}\d{2})',    # YYYYMMDD
            r'(\d{2}-\d{2}-\d{4})',  # MM-DD-YYYY
            r'(\d{2}\d{2}\d{4})'     # MMDDYYYY
        ]
        
        for pattern in patterns:
            match = re.search(pattern, filename)
            if match:
                date_str = match.group(1)
                try:
                    if '-' in date_str:
                        if len(date_str.split('-')[0]) == 4:
                            return datetime.strptime(date_str, '%Y-%m-%d').date()
                        else:
                            return datetime.strptime(date_str, '%m-%d-%Y').date()
                    else:
                        if len(date_str) == 8:
                            if date_str[:4] > '1900':
                                return datetime.strptime(date_str, '%Y%m%d').date()
                            else:
                                return datetime.strptime(date_str, '%m%d%Y').date()
                except ValueError:
                    continue
        
        # Default to today if no date found
        logger.warning(f"Could not extract date from filename {filename}, using today")
        return date.today()
    
    def group_by_key(self, components: List[MarginComponents]) -> Dict[Tuple[str, str], MarginComponents]:
        """Group margin components by (account, product) key."""
        grouped = {}
        
        for component in components:
            key = (component.account, component.product)
            
            if key in grouped:
                # Aggregate multiple series for same product
                existing = grouped[key]
                existing.scan_risk += component.scan_risk
                existing.inter_spread_charge += component.inter_spread_charge
                existing.short_opt_minimum += component.short_opt_minimum
                existing.long_opt_credit += component.long_opt_credit
                existing.net_premium += component.net_premium
                existing.add_on_margin += component.add_on_margin
                existing.total_margin += component.total_margin
                existing.net_position += component.net_position
            else:
                grouped[key] = component
        
        return grouped
