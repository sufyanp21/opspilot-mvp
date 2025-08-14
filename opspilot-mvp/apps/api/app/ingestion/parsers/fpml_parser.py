"""FpML 5.x parser for vanilla IRS and FX Forward confirmations."""

from typing import Dict, List, Optional, Any, Union
from datetime import date, datetime
from decimal import Decimal
from dataclasses import dataclass
import logging
from pathlib import Path
import zipfile
import io

from lxml import etree
from lxml.etree import _Element

logger = logging.getLogger(__name__)


# FpML 5.x namespace mappings
FPML_NAMESPACES = {
    'fpml': 'http://www.fpml.org/FpML-5/confirmation',
    'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
}


@dataclass
class CanonicalTrade:
    """Canonical trade representation for OTC instruments."""
    trade_id: str
    trade_date: date
    counterparty: str
    product_type: str  # 'IRS' or 'FX_FWD'
    uti: Optional[str] = None
    
    # Common fields
    notional: Optional[Decimal] = None
    currency: Optional[str] = None
    
    # IRS specific
    effective_date: Optional[date] = None
    maturity_date: Optional[date] = None
    fixed_rate: Optional[Decimal] = None
    floating_index: Optional[str] = None
    floating_spread: Optional[Decimal] = None
    pay_receive: Optional[str] = None  # 'PAY' or 'RECEIVE'
    day_count: Optional[str] = None
    
    # FX Forward specific
    currency1: Optional[str] = None
    currency2: Optional[str] = None
    notional1: Optional[Decimal] = None
    notional2: Optional[Decimal] = None
    forward_rate: Optional[Decimal] = None
    value_date: Optional[date] = None
    
    # Metadata
    source_file: Optional[str] = None
    parsed_at: Optional[datetime] = None


@dataclass
class PaymentSchedule:
    """Payment schedule for IRS legs."""
    start_date: date
    end_date: date
    frequency: str  # 'M', 'Q', 'S', 'A'
    day_count: str
    business_day_convention: str = 'MODFOLLOWING'


class FpMLParser:
    """Parser for FpML 5.x confirmation documents."""
    
    def __init__(self):
        self.currency_normalizer = CurrencyNormalizer()
        self.daycount_normalizer = DayCountNormalizer()
    
    def parse_file(self, file_path: str) -> List[CanonicalTrade]:
        """
        Parse FpML file(s) and return canonical trades.
        
        Args:
            file_path: Path to FpML XML file or ZIP archive
            
        Returns:
            List of canonical trades
        """
        try:
            file_path_obj = Path(file_path)
            
            if file_path_obj.suffix.lower() == '.zip':
                return self._parse_zip_file(file_path)
            else:
                return self._parse_xml_file(file_path)
                
        except Exception as e:
            logger.error(f"Error parsing FpML file {file_path}: {e}")
            raise
    
    def parse_xml_content(self, xml_content: str, source_file: str = None) -> List[CanonicalTrade]:
        """
        Parse FpML XML content string.
        
        Args:
            xml_content: FpML XML content
            source_file: Optional source file name for metadata
            
        Returns:
            List of canonical trades
        """
        try:
            root = etree.fromstring(xml_content.encode('utf-8'))
            return self._parse_fpml_document(root, source_file)
            
        except etree.XMLSyntaxError as e:
            logger.error(f"Invalid XML syntax: {e}")
            raise ValueError(f"Invalid FpML XML: {e}")
        except Exception as e:
            logger.error(f"Error parsing FpML content: {e}")
            raise
    
    def _parse_zip_file(self, zip_path: str) -> List[CanonicalTrade]:
        """Parse ZIP file containing multiple FpML documents."""
        trades = []
        
        with zipfile.ZipFile(zip_path, 'r') as zip_file:
            for file_info in zip_file.infolist():
                if file_info.filename.lower().endswith('.xml'):
                    logger.info(f"Parsing {file_info.filename} from ZIP")
                    
                    with zip_file.open(file_info) as xml_file:
                        xml_content = xml_file.read().decode('utf-8')
                        file_trades = self.parse_xml_content(xml_content, file_info.filename)
                        trades.extend(file_trades)
        
        return trades
    
    def _parse_xml_file(self, xml_path: str) -> List[CanonicalTrade]:
        """Parse single FpML XML file."""
        with open(xml_path, 'r', encoding='utf-8') as f:
            xml_content = f.read()
        
        return self.parse_xml_content(xml_content, Path(xml_path).name)
    
    def _parse_fpml_document(self, root: _Element, source_file: str = None) -> List[CanonicalTrade]:
        """Parse FpML document root element."""
        trades = []
        
        # Handle both single trade and portfolio documents
        trade_elements = root.xpath('//fpml:trade', namespaces=FPML_NAMESPACES)
        
        if not trade_elements:
            raise ValueError("No trade elements found in FpML document")
        
        for trade_elem in trade_elements:
            try:
                trade = self._parse_trade_element(trade_elem, source_file)
                if trade:
                    trades.append(trade)
            except Exception as e:
                logger.error(f"Error parsing trade element: {e}")
                # Continue parsing other trades
                continue
        
        return trades
    
    def _parse_trade_element(self, trade_elem: _Element, source_file: str = None) -> Optional[CanonicalTrade]:
        """Parse individual trade element."""
        try:
            # Extract trade header information
            trade_header = trade_elem.xpath('.//fpml:tradeHeader', namespaces=FPML_NAMESPACES)[0]
            
            trade_id = self._get_text(trade_header, './/fpml:partyTradeIdentifier/fpml:tradeId')
            trade_date_str = self._get_text(trade_header, './/fpml:tradeDate')
            trade_date = self._parse_date(trade_date_str)
            
            # Extract counterparty
            counterparty = self._get_text(trade_header, './/fpml:partyTradeIdentifier/fpml:partyReference/@href')
            if not counterparty:
                counterparty = "UNKNOWN"
            
            # Extract UTI if present
            uti = self._get_text(trade_elem, './/fpml:usi/fpml:utiIdentifier')
            
            # Determine product type and parse accordingly
            if trade_elem.xpath('.//fpml:swap', namespaces=FPML_NAMESPACES):
                return self._parse_irs_trade(trade_elem, trade_id, trade_date, counterparty, uti, source_file)
            elif trade_elem.xpath('.//fpml:fxSingleLeg', namespaces=FPML_NAMESPACES):
                return self._parse_fx_forward_trade(trade_elem, trade_id, trade_date, counterparty, uti, source_file)
            else:
                logger.warning(f"Unsupported product type in trade {trade_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error parsing trade element: {e}")
            raise
    
    def _parse_irs_trade(
        self, 
        trade_elem: _Element, 
        trade_id: str, 
        trade_date: date, 
        counterparty: str, 
        uti: Optional[str],
        source_file: str = None
    ) -> CanonicalTrade:
        """Parse Interest Rate Swap trade."""
        try:
            swap_elem = trade_elem.xpath('.//fpml:swap', namespaces=FPML_NAMESPACES)[0]
            swap_streams = swap_elem.xpath('.//fpml:swapStream', namespaces=FPML_NAMESPACES)
            
            if len(swap_streams) != 2:
                raise ValueError(f"Expected 2 swap streams, found {len(swap_streams)}")
            
            # Identify fixed and floating legs
            fixed_leg = None
            floating_leg = None
            
            for stream in swap_streams:
                if stream.xpath('.//fpml:fixedRateSchedule', namespaces=FPML_NAMESPACES):
                    fixed_leg = stream
                elif stream.xpath('.//fpml:floatingRateCalculation', namespaces=FPML_NAMESPACES):
                    floating_leg = stream
            
            if not fixed_leg or not floating_leg:
                raise ValueError("Could not identify fixed and floating legs")
            
            # Extract common swap details
            effective_date_str = self._get_text(swap_elem, './/fpml:effectiveDate/fpml:unadjustedDate')
            effective_date = self._parse_date(effective_date_str)
            
            maturity_date_str = self._get_text(swap_elem, './/fpml:terminationDate/fpml:unadjustedDate')
            maturity_date = self._parse_date(maturity_date_str)
            
            # Extract notional (assuming same for both legs)
            notional_str = self._get_text(fixed_leg, './/fpml:notionalSchedule/fpml:notionalStepSchedule/fpml:initialValue')
            notional = Decimal(notional_str) if notional_str else None
            
            currency = self._get_text(fixed_leg, './/fpml:notionalSchedule/fpml:notionalStepSchedule/fpml:currency')
            currency = self.currency_normalizer.normalize(currency)
            
            # Extract fixed rate
            fixed_rate_str = self._get_text(fixed_leg, './/fpml:fixedRateSchedule/fpml:initialValue')
            fixed_rate = Decimal(fixed_rate_str) if fixed_rate_str else None
            
            # Extract floating details
            floating_index = self._get_text(floating_leg, './/fpml:floatingRateCalculation/fpml:floatingRateIndex')
            floating_spread_str = self._get_text(floating_leg, './/fpml:floatingRateCalculation/fpml:spread')
            floating_spread = Decimal(floating_spread_str) if floating_spread_str else Decimal('0')
            
            # Determine pay/receive from payer/receiver party references
            fixed_payer = self._get_text(fixed_leg, './/fpml:payerPartyReference/@href')
            pay_receive = "PAY" if fixed_payer == counterparty else "RECEIVE"
            
            # Extract day count convention
            day_count_raw = self._get_text(fixed_leg, './/fpml:dayCountFraction')
            day_count = self.daycount_normalizer.normalize(day_count_raw)
            
            return CanonicalTrade(
                trade_id=trade_id,
                trade_date=trade_date,
                counterparty=counterparty,
                product_type="IRS",
                uti=uti,
                notional=notional,
                currency=currency,
                effective_date=effective_date,
                maturity_date=maturity_date,
                fixed_rate=fixed_rate,
                floating_index=floating_index,
                floating_spread=floating_spread,
                pay_receive=pay_receive,
                day_count=day_count,
                source_file=source_file,
                parsed_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Error parsing IRS trade {trade_id}: {e}")
            raise
    
    def _parse_fx_forward_trade(
        self, 
        trade_elem: _Element, 
        trade_id: str, 
        trade_date: date, 
        counterparty: str, 
        uti: Optional[str],
        source_file: str = None
    ) -> CanonicalTrade:
        """Parse FX Forward trade."""
        try:
            fx_elem = trade_elem.xpath('.//fpml:fxSingleLeg', namespaces=FPML_NAMESPACES)[0]
            
            # Extract value date
            value_date_str = self._get_text(fx_elem, './/fpml:valueDate')
            value_date = self._parse_date(value_date_str)
            
            # Extract currency amounts
            currency1 = self._get_text(fx_elem, './/fpml:exchangedCurrency1/fpml:paymentAmount/fpml:currency')
            currency1 = self.currency_normalizer.normalize(currency1)
            
            notional1_str = self._get_text(fx_elem, './/fpml:exchangedCurrency1/fpml:paymentAmount/fpml:amount')
            notional1 = Decimal(notional1_str) if notional1_str else None
            
            currency2 = self._get_text(fx_elem, './/fpml:exchangedCurrency2/fpml:paymentAmount/fpml:currency')
            currency2 = self.currency_normalizer.normalize(currency2)
            
            notional2_str = self._get_text(fx_elem, './/fpml:exchangedCurrency2/fpml:paymentAmount/fpml:amount')
            notional2 = Decimal(notional2_str) if notional2_str else None
            
            # Calculate forward rate (currency2/currency1)
            forward_rate = None
            if notional1 and notional2 and notional1 != 0:
                forward_rate = notional2 / notional1
            
            return CanonicalTrade(
                trade_id=trade_id,
                trade_date=trade_date,
                counterparty=counterparty,
                product_type="FX_FWD",
                uti=uti,
                currency1=currency1,
                currency2=currency2,
                notional1=notional1,
                notional2=notional2,
                forward_rate=forward_rate,
                value_date=value_date,
                source_file=source_file,
                parsed_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Error parsing FX Forward trade {trade_id}: {e}")
            raise
    
    def _get_text(self, element: _Element, xpath: str) -> Optional[str]:
        """Get text content from XPath, handling namespaces."""
        try:
            result = element.xpath(xpath, namespaces=FPML_NAMESPACES)
            if result:
                if isinstance(result[0], str):
                    return result[0].strip()
                else:
                    return result[0].text.strip() if result[0].text else None
            return None
        except Exception:
            return None
    
    def _parse_date(self, date_str: str) -> Optional[date]:
        """Parse date string in various formats."""
        if not date_str:
            return None
        
        # Try common date formats
        formats = ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%Y%m%d']
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        
        raise ValueError(f"Unable to parse date: {date_str}")


class CurrencyNormalizer:
    """Normalize currency codes to ISO 4217 standard."""
    
    def __init__(self):
        self.currency_mappings = {
            'USD': 'USD',
            'EUR': 'EUR', 
            'GBP': 'GBP',
            'JPY': 'JPY',
            'CHF': 'CHF',
            'CAD': 'CAD',
            'AUD': 'AUD',
            'NZD': 'NZD',
            # Add more mappings as needed
        }
    
    def normalize(self, currency: str) -> str:
        """Normalize currency code."""
        if not currency:
            return currency
        
        currency_upper = currency.upper().strip()
        return self.currency_mappings.get(currency_upper, currency_upper)


class DayCountNormalizer:
    """Normalize day count conventions to standard forms."""
    
    def __init__(self):
        self.daycount_mappings = {
            'ACT/360': 'ACT/360',
            'ACTUAL/360': 'ACT/360',
            'ACT/365': 'ACT/365',
            'ACTUAL/365': 'ACT/365',
            'ACT/ACT': 'ACT/ACT',
            'ACTUAL/ACTUAL': 'ACT/ACT',
            '30/360': '30/360',
            '30E/360': '30E/360',
            # Add more mappings as needed
        }
    
    def normalize(self, daycount: str) -> str:
        """Normalize day count convention."""
        if not daycount:
            return daycount
        
        daycount_upper = daycount.upper().strip()
        return self.daycount_mappings.get(daycount_upper, daycount_upper)


class FpMLValidationError(Exception):
    """Exception raised for FpML validation errors."""
    
    def __init__(self, message: str, xpath: str = None):
        self.xpath = xpath
        super().__init__(message)
    
    def __str__(self):
        if self.xpath:
            return f"{super().__str__()} (at {self.xpath})"
        return super().__str__()
