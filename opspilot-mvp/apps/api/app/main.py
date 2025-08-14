from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import uvicorn

from app.core.config import settings
from app.core.logging import setup_logging
from app.api.v1 import upload, reconcile, span, margin, otc, exceptions, audit
from app.api.v1 import files, health
from app.db.session import engine
from app.models import base

# Setup logging
setup_logging()

# Create FastAPI app
app = FastAPI(
    title="OpsPilot MVP API",
    description="Derivatives Data Automation Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure appropriately for production
)

# Include routers
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(files.router, prefix="/api/v1", tags=["files"])
app.include_router(reconcile.router, prefix="/api/v1", tags=["reconcile"])
app.include_router(span.router, prefix="/api/v1", tags=["span"])
app.include_router(margin.router, prefix="/api/v1", tags=["margin"])
app.include_router(otc.router, prefix="/api/v1", tags=["otc"])
app.include_router(exceptions.router, prefix="/api/v1", tags=["exceptions"])
app.include_router(audit.router, prefix="/api/v1", tags=["audit"])

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    # Create database tables
    base.Base.metadata.create_all(bind=engine)

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    pass

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if settings.APP_ENV == "dev" else False,
    )
