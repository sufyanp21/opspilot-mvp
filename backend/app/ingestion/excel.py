from __future__ import annotations

from typing import List

import pandas as pd

from .csv import parse_trade_csv


def parse_trade_excel(content: bytes) -> List:
    df = pd.read_excel(pd.io.common.BytesIO(content))
    return parse_trade_csv(df)


