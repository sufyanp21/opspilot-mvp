from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import uuid
import json

from app.db.session import get_db
from app.models.file import SourceFile
from app.models.recon import ReconRun, ReconException, ReconStatus, ExceptionStatus
from app.services.recon_service import ReconciliationService
from app.core.logging import logger

router = APIRouter()

class ColumnMapping(BaseModel):
    internal: Dict[str, str]
    cleared: Dict[str, str]

class ToleranceConfig(BaseModel):
    price_ticks: int = 1
    qty: int = 0

class ReconcileRequest(BaseModel):
    internal_file_id: str
    cleared_file_id: str
    column_map: ColumnMapping
    match_keys: List[str] = ["trade_date", "account", "symbol"]
    tolerances: ToleranceConfig = ToleranceConfig()

class ExceptionInfo(BaseModel):
    id: str
    keys: Dict[str, Any]
    internal: Optional[Dict[str, Any]]
    cleared: Optional[Dict[str, Any]]
    diff: Optional[Dict[str, Any]]
    status: str

class ReconcileSummary(BaseModel):
    total: int
    matched: int
    mismatched: int
    pct_matched: float

class ReconcileResponse(BaseModel):
    run_id: str
    summary: ReconcileSummary
    exceptions: List[ExceptionInfo]

class ReconRunInfo(BaseModel):
    id: str
    status: str
    started_at: str
    finished_at: Optional[str]
    internal_file_id: str
    cleared_file_id: str
    summary: Optional[ReconcileSummary]

@router.post("/reconcile", response_model=ReconcileResponse)
async def run_reconciliation(
    request: ReconcileRequest,
    db: Session = Depends(get_db)
):
    """Run reconciliation between internal and cleared files."""
    
    try:
        # Validate file IDs
        internal_uuid = uuid.UUID(request.internal_file_id)
        cleared_uuid = uuid.UUID(request.cleared_file_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid file ID format")
    
    # Check files exist
    internal_file = db.query(SourceFile).filter(SourceFile.id == internal_uuid).first()
    cleared_file = db.query(SourceFile).filter(SourceFile.id == cleared_uuid).first()
    
    if not internal_file:
        raise HTTPException(status_code=404, detail="Internal file not found")
    if not cleared_file:
        raise HTTPException(status_code=404, detail="Cleared file not found")
    
    try:
        # Create reconciliation run record
        run_id = uuid.uuid4()
        recon_run = ReconRun(
            id=run_id,
            internal_file_id=internal_uuid,
            cleared_file_id=cleared_uuid,
            column_map=json.dumps(request.column_map.dict()),
            match_keys=json.dumps(request.match_keys),
            tolerances=json.dumps(request.tolerances.dict()),
            status=ReconStatus.RUNNING
        )
        
        db.add(recon_run)
        db.commit()
        
        # Run reconciliation
        recon_service = ReconciliationService(db)
        result = await recon_service.run_reconciliation(
            run_id=run_id,
            internal_file=internal_file,
            cleared_file=cleared_file,
            column_map=request.column_map.dict(),
            match_keys=request.match_keys,
            tolerances=request.tolerances.dict()
        )
        
        # Update run status
        recon_run.status = ReconStatus.COMPLETED
        recon_run.summary_json = json.dumps(result["summary"])
        db.commit()
        
        logger.info(f"Reconciliation completed: {run_id}")
        
        return ReconcileResponse(
            run_id=str(run_id),
            summary=ReconcileSummary(**result["summary"]),
            exceptions=[
                ExceptionInfo(
                    id=str(exc["id"]),
                    keys=exc["keys"],
                    internal=exc["internal"],
                    cleared=exc["cleared"],
                    diff=exc["diff"],
                    status=exc["status"]
                ) for exc in result["exceptions"]
            ]
        )
        
    except Exception as e:
        # Update run status to failed
        if 'recon_run' in locals():
            recon_run.status = ReconStatus.FAILED
            recon_run.error_message = str(e)
            db.commit()
        
        logger.error(f"Reconciliation failed: {e}")
        raise HTTPException(status_code=500, detail="Reconciliation failed")

@router.get("/reconcile/runs", response_model=List[ReconRunInfo])
async def list_reconciliation_runs(db: Session = Depends(get_db)):
    """List all reconciliation runs."""
    
    runs = db.query(ReconRun).order_by(ReconRun.created_at.desc()).all()
    
    result = []
    for run in runs:
        summary = None
        if run.summary_json:
            try:
                summary_data = json.loads(run.summary_json)
                summary = ReconcileSummary(**summary_data)
            except:
                pass
        
        result.append(ReconRunInfo(
            id=str(run.id),
            status=run.status.value,
            started_at=run.started_at.isoformat(),
            finished_at=run.finished_at.isoformat() if run.finished_at else None,
            internal_file_id=str(run.internal_file_id),
            cleared_file_id=str(run.cleared_file_id),
            summary=summary
        ))
    
    return result

@router.get("/reconcile/runs/{run_id}/exceptions", response_model=List[ExceptionInfo])
async def get_run_exceptions(run_id: str, db: Session = Depends(get_db)):
    """Get exceptions for a specific reconciliation run."""
    
    try:
        run_uuid = uuid.UUID(run_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid run ID format")
    
    exceptions = db.query(ReconException).filter(ReconException.run_id == run_uuid).all()
    
    result = []
    for exc in exceptions:
        keys = json.loads(exc.keys_json) if exc.keys_json else {}
        internal = json.loads(exc.internal_json) if exc.internal_json else None
        cleared = json.loads(exc.cleared_json) if exc.cleared_json else None
        diff = json.loads(exc.diff_json) if exc.diff_json else None
        
        result.append(ExceptionInfo(
            id=str(exc.id),
            keys=keys,
            internal=internal,
            cleared=cleared,
            diff=diff,
            status=exc.status.value
        ))
    
    return result
