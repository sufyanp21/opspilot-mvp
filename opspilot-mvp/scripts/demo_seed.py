#!/usr/bin/env python3
"""
Demo seed script for OpsPilot MVP
Generates realistic sample data for ETD, OTC, and SPAN to showcase all features.
"""

import os
import sys
import csv
import json
import uuid
import random
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import List, Dict, Any

# Add the backend app to Python path
sys.path.append(str(Path(__file__).parent.parent / "apps" / "backend"))


class DemoDataGenerator:
    """Generates realistic demo data for OpsPilot MVP."""
    
    def __init__(self):
        self.demo_date = datetime.now().date()
        self.accounts = ["PROP_DESK", "CLIENT_A", "CLIENT_B", "HEDGE_FUND_1", "PENSION_FUND"]
        self.symbols = {
            "ETD": ["ES", "NQ", "YM", "RTY", "ZN", "ZB", "ZF", "GC", "SI", "CL"],
            "OTC": ["USD.IRS.5Y", "EUR.IRS.10Y", "GBP.IRS.2Y", "EURUSD.FX.3M", "GBPUSD.FX.6M"]
        }
        self.exchanges = ["CME", "CBOT", "NYMEX", "ICE"]
        self.counterparties = ["GOLDMAN", "JPMORGAN", "CITI", "BARCLAYS", "DEUTSCHE"]
        
        # Create demo directories
        self.demo_dir = Path(__file__).parent.parent / "demo_data"
        self.demo_dir.mkdir(exist_ok=True)
        (self.demo_dir / "internal").mkdir(exist_ok=True)
        (self.demo_dir / "cleared").mkdir(exist_ok=True)
        (self.demo_dir / "span").mkdir(exist_ok=True)
        (self.demo_dir / "otc").mkdir(exist_ok=True)
    
    def generate_etd_trades(self, count: int = 1000, file_type: str = "internal") -> str:
        """Generate ETD trades CSV file."""
        filename = f"etd_trades_{file_type}_{self.demo_date.strftime('%Y%m%d')}.csv"
        filepath = self.demo_dir / file_type / filename
        
        trades = []
        base_trade_id = 100000 if file_type == "internal" else 200000
        
        for i in range(count):
            symbol = random.choice(self.symbols["ETD"])
            account = random.choice(self.accounts)
            side = random.choice(["BUY", "SELL"])
            qty = random.randint(1, 100)
            
            # Base price with some variation
            base_prices = {
                "ES": 4500.00, "NQ": 15000.00, "YM": 35000.00, "RTY": 2000.00,
                "ZN": 110.50, "ZB": 125.25, "ZF": 105.75,
                "GC": 2000.00, "SI": 25.00, "CL": 75.00
            }
            
            base_price = base_prices.get(symbol, 100.00)
            price_variation = random.uniform(-0.05, 0.05)  # ±5% variation
            price = round(base_price * (1 + price_variation), 2)
            
            # Add some intentional breaks for demo
            if file_type == "cleared" and random.random() < 0.05:  # 5% break rate
                if random.random() < 0.5:
                    price += random.choice([0.25, 0.50, 0.75])  # Price breaks
                else:
                    qty += random.choice([1, 2, 5])  # Quantity breaks
            
            trade = {
                "trade_id": f"T{base_trade_id + i:06d}",
                "trade_date": self.demo_date.strftime("%Y-%m-%d"),
                "account": account,
                "symbol": symbol,
                "side": side,
                "qty": qty,
                "price": price,
                "exchange": random.choice(self.exchanges),
                "clearing_ref": f"CLR{random.randint(1000000, 9999999)}" if file_type == "cleared" else "",
                "settlement_date": (self.demo_date + timedelta(days=1)).strftime("%Y-%m-%d"),
                "trader": f"TRADER_{random.randint(1, 10)}"
            }
            trades.append(trade)
        
        # Write CSV file
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            if trades:
                writer = csv.DictWriter(f, fieldnames=trades[0].keys())
                writer.writeheader()
                writer.writerows(trades)
        
        print(f"✅ Generated {count} ETD {file_type} trades: {filename}")
        return str(filepath)
    
    def generate_otc_fpml(self, count: int = 50) -> str:
        """Generate OTC FpML file with IRS and FX trades."""
        filename = f"otc_trades_{self.demo_date.strftime('%Y%m%d')}.xml"
        filepath = self.demo_dir / "otc" / filename
        
        # Simple FpML structure for demo
        fpml_content = '''<?xml version="1.0" encoding="utf-8"?>
<dataDocument xmlns="http://www.fpml.org/FpML-5/confirmation" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <trade>
        <tradeHeader>
            <partyTradeIdentifier>
                <partyReference href="party1"/>
                <tradeId tradeIdScheme="http://www.example.com/trade-id">IRS001</tradeId>
            </partyTradeIdentifier>
            <tradeDate>2024-01-15</tradeDate>
        </tradeHeader>
        <swap>
            <swapStream id="fixedLeg">
                <payerPartyReference href="party1"/>
                <receiverPartyReference href="party2"/>
                <calculationPeriodAmount>
                    <calculation>
                        <notionalSchedule>
                            <notionalStepSchedule>
                                <initialValue>10000000</initialValue>
                                <currency>USD</currency>
                            </notionalStepSchedule>
                        </notionalSchedule>
                        <fixedRateSchedule>
                            <initialValue>0.0350</initialValue>
                        </fixedRateSchedule>
                    </calculation>
                </calculationPeriodAmount>
            </swapStream>
            <swapStream id="floatingLeg">
                <payerPartyReference href="party2"/>
                <receiverPartyReference href="party1"/>
                <calculationPeriodAmount>
                    <calculation>
                        <notionalSchedule>
                            <notionalStepSchedule>
                                <initialValue>10000000</initialValue>
                                <currency>USD</currency>
                            </notionalStepSchedule>
                        </notionalSchedule>
                        <floatingRateCalculation>
                            <floatingRateIndex>USD-LIBOR-BBA</floatingRateIndex>
                            <indexTenor>
                                <periodMultiplier>3</periodMultiplier>
                                <period>M</period>
                            </indexTenor>
                        </floatingRateCalculation>
                    </calculation>
                </calculationPeriodAmount>
            </swapStream>
        </swap>
    </trade>
</dataDocument>'''
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(fpml_content)
        
        print(f"✅ Generated OTC FpML file: {filename}")
        return str(filepath)
    
    def generate_span_margins(self, count: int = 500) -> str:
        """Generate SPAN margin data CSV file."""
        filename = f"span_margins_{self.demo_date.strftime('%Y%m%d')}.csv"
        filepath = self.demo_dir / "span" / filename
        
        margins = []
        
        for i in range(count):
            account = random.choice(self.accounts)
            symbol = random.choice(self.symbols["ETD"])
            
            # Generate realistic margin amounts
            base_margins = {
                "ES": 12000, "NQ": 18000, "YM": 8000, "RTY": 6000,
                "ZN": 2500, "ZB": 3500, "ZF": 1800,
                "GC": 8500, "SI": 15000, "CL": 4200
            }
            
            base_margin = base_margins.get(symbol, 5000)
            initial_margin = base_margin + random.randint(-500, 500)
            maintenance_margin = int(initial_margin * 0.75)
            
            margin = {
                "as_of_date": self.demo_date.strftime("%Y-%m-%d"),
                "account": account,
                "symbol": symbol,
                "exchange": random.choice(self.exchanges),
                "product_type": "FUTURE",
                "currency": "USD",
                "initial_margin": initial_margin,
                "maintenance_margin": maintenance_margin,
                "span_requirement": initial_margin + random.randint(-200, 200),
                "price_scan_range": random.randint(800, 1200),
                "volatility_scan_range": random.randint(600, 1000),
                "inter_month_spread": random.randint(100, 300),
                "inter_commodity_spread": random.randint(50, 150),
                "short_option_minimum": random.randint(25, 75)
            }
            margins.append(margin)
        
        # Write CSV file
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            if margins:
                writer = csv.DictWriter(f, fieldnames=margins[0].keys())
                writer.writeheader()
                writer.writerows(margins)
        
        print(f"✅ Generated {count} SPAN margin records: {filename}")
        return str(filepath)
    
    def generate_all_demo_data(self):
        """Generate complete demo dataset."""
        print("🚀 Generating OpsPilot MVP Demo Data...")
        print("=" * 50)
        
        # Generate ETD data
        print("\n📊 Generating ETD Trade Data:")
        internal_etd = self.generate_etd_trades(1000, "internal")
        cleared_etd = self.generate_etd_trades(950, "cleared")  # Slightly fewer to create breaks
        
        # Generate OTC data
        print("\n💱 Generating OTC FpML Data:")
        otc_fpml = self.generate_otc_fpml(50)
        
        # Generate SPAN data
        print("\n📈 Generating SPAN Margin Data:")
        span_margins = self.generate_span_margins(500)
        
        print("\n" + "=" * 50)
        print("✅ Demo data generation complete!")
        print(f"📁 Data location: {self.demo_dir}")
        print("\nGenerated files:")
        print(f"  • Internal ETD: {Path(internal_etd).name}")
        print(f"  • Cleared ETD: {Path(cleared_etd).name}")
        print(f"  • OTC FpML: {Path(otc_fpml).name}")
        print(f"  • SPAN Margins: {Path(span_margins).name}")
        
        return {
            "internal_etd": internal_etd,
            "cleared_etd": cleared_etd,
            "otc_fpml": otc_fpml,
            "span_margins": span_margins
        }


def main():
    """Main demo seed function."""
    try:
        generator = DemoDataGenerator()
        files = generator.generate_all_demo_data()
        
        print("\n🎯 Next Steps:")
        print("1. Run the demo script: python scripts/demo_run.py")
        print("2. Or manually upload files through the UI")
        print("3. Navigate to http://localhost:3000 to see the demo")
        
        return files
        
    except Exception as e:
        print(f"❌ Error generating demo data: {e}")
        return None


if __name__ == "__main__":
    main()
