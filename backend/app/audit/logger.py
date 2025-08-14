from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class AuditLogger:
    base_dir: Path

    def __post_init__(self) -> None:
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._log_path = self.base_dir / "audit.jsonl"
        self._prev_hash_path = self.base_dir / "prev.hash"

    def _get_prev_hash(self) -> str:
        if self._prev_hash_path.exists():
            return self._prev_hash_path.read_text().strip()
        return "0" * 64

    def _write_prev_hash(self, h: str) -> None:
        self._prev_hash_path.write_text(h)

    def write_event(
        self,
        action: str,
        metadata: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
    ) -> None:
        event = {
            "time": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "metadata": metadata or {},
            "correlation_id": correlation_id,
        }
        prev_hash = self._get_prev_hash()
        payload = json.dumps({"prev": prev_hash, "event": event}, separators=(",", ":"))
        event_hash = hashlib.sha256(payload.encode()).hexdigest()
        event_record = {"hash": event_hash, "prev": prev_hash, **event}
        with self._log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event_record) + "\n")
        self._write_prev_hash(event_hash)


