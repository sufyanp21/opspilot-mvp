from sqlalchemy import Column, String, DateTime, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import enum

from app.models.base import BaseModel

class FileKind(str, enum.Enum):
    INTERNAL = "internal"
    CLEARED = "cleared"
    SPAN = "span"

class SourceFile(BaseModel):
    """Model for uploaded files."""
    __tablename__ = "source_files"
    
    kind = Column(SQLEnum(FileKind), nullable=False)
    original_name = Column(String(255), nullable=False)
    stored_path = Column(String(500), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    uploaded_by = Column(String(255), nullable=True)
    
    # File metadata
    file_size = Column(String(50), nullable=True)  # File size in bytes
    content_type = Column(String(100), nullable=True)
    
    # Processing status
    processing_status = Column(String(50), default="pending", nullable=False)
    processing_error = Column(Text, nullable=True)
    
    # Column information (JSON stored as text)
    columns_detected = Column(Text, nullable=True)  # JSON string of detected columns
