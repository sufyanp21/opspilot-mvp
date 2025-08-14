from __future__ import annotations

import csv
import io
from typing import List, Dict, Any


def exceptions_to_csv(exceptions: List[Dict[str, Any]]) -> bytes:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["type", "severity", "trade_id", "cluster", "details"])
    writer.writeheader()
    for ex in exceptions:
        writer.writerow(
            {
                "type": ex.get("type"),
                "severity": ex.get("severity"),
                "trade_id": ex.get("trade_id"),
                "cluster": ex.get("cluster"),
                "details": json_dumps_safe(ex.get("details")),
            }
        )
    return output.getvalue().encode()


def json_dumps_safe(value: Any) -> str:
    try:
        import json

        return json.dumps(value)
    except Exception:
        return str(value)


