import pandas as pd

from app.ingestion.csv import parse_trade_csv


def test_parse_trade_csv_ok():
    df = pd.DataFrame(
        [
            {"trade_id": "T1", "product_code": "ES", "quantity": 1, "price": 5000.0},
            {"trade_id": "T2", "product_code": "NQ", "quantity": 2, "price": 15000.0},
        ]
    )
    trades = parse_trade_csv(df)
    assert len(trades) == 2
    assert trades[0].trade_id == "T1"


def test_parse_trade_csv_missing_columns():
    df = pd.DataFrame([{"trade": "T1"}])
    try:
        parse_trade_csv(df)
        assert False, "expected ValueError"
    except ValueError:
        assert True


