from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import os
import uuid
import json
import pandas as pd

from app.db.session import get_db
from app.models.file import SourceFile, FileKind
from app.core.config import settings
from app.core.logging import logger

router = APIRouter()

class FileUploadResponse(BaseModel):
    file_id: str
    columns: List[str]

class FileInfo(BaseModel):
    id: str
    kind: str
    original_name: str
    uploaded_at: str
    processing_status: str
    columns: Optional[List[str]] = None

@router.post("/files/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    kind: str = Form(...),
    db: Session = Depends(get_db)
):
    """Upload a file for processing."""
    
    # Validate kind
    try:
        file_kind = FileKind(kind)
    except ValueError:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid file kind. Must be one of: {[k.value for k in FileKind]}"
        )
    
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
        
        # Read CSV to detect columns
        try:
            df = pd.read_csv(stored_path, nrows=0)  # Read only headers
            columns = df.columns.tolist()
        except Exception as e:
            logger.error(f"Failed to read CSV columns: {e}")
            columns = []
        
        # Create database record
        source_file = SourceFile(
            id=uuid.UUID(file_id),
            kind=file_kind,
            original_name=file.filename,
            stored_path=stored_path,
            file_size=str(len(content)),
            content_type=file.content_type,
            processing_status="completed",
            columns_detected=json.dumps(columns)
        )
        
        db.add(source_file)
        db.commit()
        
        logger.info(f"File uploaded successfully: {file.filename} -> {file_id}")
        
        return FileUploadResponse(
            file_id=file_id,
            columns=columns
        )
        
    except Exception as e:
        logger.error(f"File upload failed: {e}")
        raise HTTPException(status_code=500, detail="File upload failed")

@router.get("/files", response_model=List[FileInfo])
async def list_files(db: Session = Depends(get_db)):
    """List all uploaded files."""
    
    files = db.query(SourceFile).order_by(SourceFile.created_at.desc()).all()
    
    result = []
    for file in files:
        columns = None
        if file.columns_detected:
            try:
                columns = json.loads(file.columns_detected)
            except:
                pass
        
        result.append(FileInfo(
            id=str(file.id),
            kind=file.kind.value,
            original_name=file.original_name,
            uploaded_at=file.created_at.isoformat(),
            processing_status=file.processing_status,
            columns=columns
        ))
    
    return result

@router.get("/files/{file_id}", response_model=FileInfo)
async def get_file(file_id: str, db: Session = Depends(get_db)):
    """Get file information by ID."""
    
    try:
        file_uuid = uuid.UUID(file_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid file ID format")
    
    file = db.query(SourceFile).filter(SourceFile.id == file_uuid).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    columns = None
    if file.columns_detected:
        try:
            columns = json.loads(file.columns_detected)
        except:
            pass
    
    return FileInfo(
        id=str(file.id),
        kind=file.kind.value,
        original_name=file.original_name,
        uploaded_at=file.created_at.isoformat(),
        processing_status=file.processing_status,
        columns=columns
    )
