from __future__ import annotations

import os
from celery import Celery
from datetime import timedelta
import os
from pathlib import Path

broker_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
backend_url = broker_url

celery_app = Celery("opspilot", broker=broker_url, backend=backend_url)
celery_app.conf.timezone = "UTC"

@celery_app.task
def task_cluster_exceptions(exceptions: list[dict]):
    from .recon.cluster import cluster_exceptions
    return cluster_exceptions(exceptions)


@celery_app.task
def task_nway(payload: dict):
    from .recon.nway import reconcile_nway
    from .schemas_cdm import Trade

    def to_trades(rows):
        return [Trade(**r) for r in rows]

    return reconcile_nway(
        to_trades(payload.get("internal", [])),
        to_trades(payload.get("broker", [])),
        to_trades(payload.get("ccp", [])),
        payload.get("authoritative_order", ["ccp", "broker", "internal"]),
        payload.get("tolerances", {"price": 0.0, "quantity": 0.0}),
    )


@celery_app.task
def task_reg_export(records: list[dict], lineage: dict):
    from .reports.regulatory import validate_regulatory, build_reg_pack
    validation = validate_regulatory(records)
    return build_reg_pack(validation, lineage)


@celery_app.task
def task_process_sftp_file(payload: dict):
    """Process a single SFTP-fetched file (register + parse)."""
    from .db import SessionLocal
    from .ingestion.sftp import process_sftp_file

    db = SessionLocal() if SessionLocal else None  # type: ignore[name-defined]
    try:
        return process_sftp_file(
            db=db,
            source=payload.get("source", "sftp"),
            filename=payload["filename"],
            content=payload["content"].encode("utf-8") if isinstance(payload.get("content"), str) else payload["content"],
            force=bool(payload.get("force", False)),
        )
    finally:
        if db is not None:
            db.close()


@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):  # pragma: no cover - scheduling wiring
    # Poll local directories for CSVs as an SFTP stand-in if configured
    dirs = os.getenv("SFTP_LOCAL_DIRS")
    if dirs:
        sender.add_periodic_task(60.0, task_poll_sftp_dirs.s(dirs), name="poll_sftp_local_dirs")


@celery_app.task
def task_poll_sftp_dirs(dir_list: str):  # pragma: no cover - simple filesystem scan
    from .db import SessionLocal
    from .ingestion.sftp import process_sftp_file

    db = SessionLocal() if SessionLocal else None  # type: ignore[name-defined]
    try:
        for d in [p.strip() for p in dir_list.split(",") if p.strip()]:
            p = Path(d)
            if not p.exists() or not p.is_dir():
                continue
            for csv_path in p.glob("*.csv"):
                content = csv_path.read_bytes()
                process_sftp_file(
                    db=db,
                    source="sftp",
                    filename=csv_path.name,
                    content=content,
                    force=False,
                )
    finally:
        if db is not None:
            db.close()

