from __future__ import annotations

import pandas as pd

from app.ingestion.csv import parse_trade_csv


def test_parse_trade_csv_missing_columns_error_message():
    df = pd.DataFrame([{"trade": "T1"}])
    try:
        parse_trade_csv(df)
        assert False, "expected ValueError"
    except ValueError as e:
        assert "Missing required columns" in str(e)


