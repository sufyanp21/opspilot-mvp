from __future__ import annotations

import io
import json
import zipfile
from datetime import datetime
from typing import Any, Dict, List


REQUIRED_FIELDS = {
    "EMIR": ["trade_id", "product_code", "price", "quantity"],
    "CFTC": ["trade_id", "product_code", "price", "quantity"],
    "MiFIDII": ["trade_id", "product_code", "price", "quantity"],
}


def validate_regulatory(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    results = {}
    for regime, fields in REQUIRED_FIELDS.items():
        passes, fails = [], []
        for rec in records:
            missing = [f for f in fields if rec.get(f) in (None, "")]
            (fails if missing else passes).append({"record": rec, "missing": missing})
        results[regime] = {"passes": passes, "fails": fails}
    return results


def build_reg_pack(results: Dict[str, Any], lineage: Dict[str, Any]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        # CSV summaries per regime
        for regime, res in results.items():
            # passes
            passes_lines = ["trade_id,status\n"]
            for item in res["passes"]:
                passes_lines.append(f"{item['record'].get('trade_id')},PASS\n")
            z.writestr(f"{regime}_passes_{ts}.csv", "".join(passes_lines))

            fails_lines = ["trade_id,missing,status\n"]
            for item in res["fails"]:
                z.writestr(
                    f"{regime}_fails_{ts}.csv",
                    "".join(
                        [
                            f"{item['record'].get('trade_id')},\"{','.join(item['missing'])}\",FAIL\n",
                        ]
                    ),
                )

        # Lineage snapshot
        z.writestr("lineage.json", json.dumps(lineage, indent=2))

        # PDF summary stub (text file placeholder for demo)
        z.writestr("summary.txt", "Regulatory pack summary (PDF to be generated in production).")

    return buf.getvalue()


