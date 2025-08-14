"""Configuration loader for product and tolerance templates."""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import logging

from app.reconciliation.tolerance.numeric_tolerance import ToleranceConfig
from app.reconciliation.engines.etd_recon_engine import ReconConfig
from app.core.enums import PriceToleranceMode

logger = logging.getLogger(__name__)


class ConfigLoader:
    """Loads and manages product and reconciliation configurations."""
    
    def __init__(self, config_dir: Optional[Path] = None):
        if config_dir is None:
            config_dir = Path(__file__).parent / "templates"
        self.config_dir = Path(config_dir)
        self._config_cache: Dict[str, Dict[str, Any]] = {}
    
    def load_product_config(self, symbol: str, exchange: str) -> Optional[Dict[str, Any]]:
        """Load product configuration from template files."""
        # Try specific symbol file first
        config_file = self.config_dir / exchange.lower() / f"{symbol.lower()}_futures.yaml"
        
        if config_file.exists():
            return self._load_yaml_file(config_file)
        
        # Try generic exchange config
        exchange_config = self.config_dir / exchange.lower() / "default.yaml"
        if exchange_config.exists():
            return self._load_yaml_file(exchange_config)
        
        logger.warning(f"No configuration found for {symbol}@{exchange}")
        return None
    
    def create_recon_config(
        self,
        match_keys: list[str],
        default_price_tolerance: Dict[str, Any],
        default_qty_tolerance: Dict[str, Any],
        product_overrides: Optional[Dict[str, str]] = None
    ) -> ReconConfig:
        """Create reconciliation configuration with product overrides."""
        
        # Parse default tolerances
        price_config = self._parse_tolerance_config(default_price_tolerance)
        qty_config = self._parse_tolerance_config(default_qty_tolerance)
        
        # Load product-specific overrides
        overrides = {}
        if product_overrides:
            for symbol, exchange in product_overrides.items():
                product_config = self.load_product_config(symbol, exchange)
                if product_config and "tolerance" in product_config:
                    symbol_overrides = {}
                    
                    tolerance_config = product_config["tolerance"]
                    if "price" in tolerance_config:
                        symbol_overrides["price"] = self._parse_tolerance_config(
                            tolerance_config["price"]
                        )
                    
                    if "quantity" in tolerance_config:
                        symbol_overrides["quantity"] = self._parse_tolerance_config(
                            tolerance_config["quantity"]
                        )
                    
                    if symbol_overrides:
                        overrides[symbol] = symbol_overrides
        
        return ReconConfig(
            match_keys=match_keys,
            price_tolerance=price_config,
            quantity_tolerance=qty_config,
            product_overrides=overrides
        )
    
    def _load_yaml_file(self, file_path: Path) -> Dict[str, Any]:
        """Load and cache YAML configuration file."""
        cache_key = str(file_path)
        
        if cache_key not in self._config_cache:
            try:
                with open(file_path, 'r') as f:
                    config = yaml.safe_load(f)
                self._config_cache[cache_key] = config
                logger.info(f"Loaded configuration from {file_path}")
            except Exception as e:
                logger.error(f"Failed to load configuration from {file_path}: {e}")
                return {}
        
        return self._config_cache[cache_key]
    
    def _parse_tolerance_config(self, tolerance_dict: Dict[str, Any]) -> ToleranceConfig:
        """Parse tolerance configuration from dictionary."""
        mode_str = tolerance_dict.get("mode", "ABSOLUTE").upper()
        
        try:
            mode = PriceToleranceMode(mode_str)
        except ValueError:
            logger.warning(f"Unknown tolerance mode: {mode_str}, defaulting to ABSOLUTE")
            mode = PriceToleranceMode.ABSOLUTE
        
        max_value = tolerance_dict.get("max", 0.0)
        max_ticks = tolerance_dict.get("max_ticks")
        
        return ToleranceConfig(
            mode=mode,
            max_value=float(max_value),
            max_ticks=max_ticks
        )
    
    def get_default_product_config(self) -> Dict[str, Any]:
        """Get default product configuration for fallback."""
        return {
            "product": {
                "tick_size": 0.25,
                "tick_value": None,
                "contract_size": 1,
                "currency": "USD",
                "product_type": "ETD"
            },
            "tolerance": {
                "quantity": {
                    "mode": "ABSOLUTE",
                    "max": 0
                },
                "price": {
                    "mode": "TICKS",
                    "max_ticks": 1
                }
            },
            "match_keys": ["trade_date", "account", "symbol"]
        }
