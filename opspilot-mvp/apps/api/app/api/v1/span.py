from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import os
import uuid
import pandas as pd
from datetime import datetime, date

from app.db.session import get_db
from app.models.file import SourceFile, FileKind
from app.models.span import SpanSnapshot, SpanDelta
from app.services.span_service import SpanService
from app.core.config import settings
from app.core.logging import logger

router = APIRouter()

class SpanUploadResponse(BaseModel):
    file_id: str
    asof: str
    rows_ingested: int

class SpanDeltaInfo(BaseModel):
    product: str
    account: str
    scan_before: Optional[float]
    scan_after: float
    delta: float

@router.post("/span/upload", response_model=SpanUploadResponse)
async def upload_span_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload a SPAN margin file."""
    
    # Validate file type
    if not file.filename.lower().endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")
    
    try:
        # Create storage directory if it doesn't exist
        os.makedirs(settings.FILE_STORAGE_DIR, exist_ok=True)
        
        # Generate unique filename
        file_id = str(uuid.uuid4())
        file_extension = os.path.splitext(file.filename)[1]
        stored_filename = f"{file_id}{file_extension}"
        stored_path = os.path.join(settings.FILE_STORAGE_DIR, stored_filename)
        
        # Save file to disk
        content = await file.read()
        with open(stored_path, "wb") as f:
            f.write(content)
        
        # Create database record
        source_file = SourceFile(
            id=uuid.UUID(file_id),
            kind=FileKind.SPAN,
            original_name=file.filename,
            stored_path=stored_path,
            file_size=str(len(content)),
            content_type=file.content_type,
            processing_status="processing"
        )
        
        db.add(source_file)
        db.commit()
        
        # Process SPAN file
        span_service = SpanService(db)
        result = await span_service.process_span_file(source_file)
        
        # Update file status
        source_file.processing_status = "completed"
        db.commit()
        
        logger.info(f"SPAN file processed successfully: {file.filename} -> {file_id}")
        
        return SpanUploadResponse(
            file_id=file_id,
            asof=result["asof_date"].isoformat(),
            rows_ingested=result["rows_ingested"]
        )
        
    except Exception as e:
        logger.error(f"SPAN file upload failed: {e}")
        if 'source_file' in locals():
            source_file.processing_status = "failed"
            source_file.processing_error = str(e)
            db.commit()
        raise HTTPException(status_code=500, detail="SPAN file upload failed")

@router.get("/span/changes", response_model=List[SpanDeltaInfo])
async def get_span_changes(
    asof: str = Query(..., description="Date in YYYY-MM-DD format"),
    db: Session = Depends(get_db)
):
    """Get SPAN margin changes for a specific date."""
    
    try:
        asof_date = datetime.strptime(asof, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    # Get deltas for the specified date
    deltas = db.query(SpanDelta).filter(SpanDelta.asof_date == asof_date).all()
    
    result = []
    for delta in deltas:
        result.append(SpanDeltaInfo(
            product=delta.product,
            account=delta.account,
            scan_before=float(delta.scan_before) if delta.scan_before else None,
            scan_after=float(delta.scan_after),
            delta=float(delta.delta)
        ))
    
    return result

@router.get("/span/snapshots")
async def get_span_snapshots(
    asof: Optional[str] = Query(None, description="Date in YYYY-MM-DD format"),
    product: Optional[str] = Query(None, description="Filter by product"),
    account: Optional[str] = Query(None, description="Filter by account"),
    db: Session = Depends(get_db)
):
    """Get SPAN margin snapshots with optional filters."""
    
    query = db.query(SpanSnapshot)
    
    if asof:
        try:
            asof_date = datetime.strptime(asof, "%Y-%m-%d").date()
            query = query.filter(SpanSnapshot.asof_date == asof_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    if product:
        query = query.filter(SpanSnapshot.product == product)
    
    if account:
        query = query.filter(SpanSnapshot.account == account)
    
    snapshots = query.order_by(SpanSnapshot.asof_date.desc()).all()
    
    result = []
    for snapshot in snapshots:
        result.append({
            "id": str(snapshot.id),
            "asof_date": snapshot.asof_date.isoformat(),
            "product": snapshot.product,
            "account": snapshot.account,
            "scan_margin": float(snapshot.scan_margin)
        })
    
    return result
