from __future__ import annotations

from typing import List
import io

import httpx
import pandas as pd

from .csv import parse_trade_csv


async def fetch_and_parse_api(url: str) -> List:
    """
    Fetch CSV content from an external API endpoint and parse.
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        df = pd.read_csv(io.StringIO(resp.text))  # type: ignore[name-defined]
        return parse_trade_csv(df)


