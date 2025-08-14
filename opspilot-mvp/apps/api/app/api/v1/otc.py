"""OTC FpML processing API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import logging
import tempfile
import os
from pathlib import Path

from app.db.session import get_db
from app.ingestion.parsers.fpml_parser import FpMLParser, CanonicalTrade, FpMLValidationError
from app.reconciliation.engines.otc_recon_engine import OTCReconEngine, OTCToleranceConfig
from app.services.file_service import FileService
from app.models.source_file import SourceFile, FileKind

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/otc/fpml")
async def upload_fpml_file(
    file: UploadFile = File(...),
    counterparty: Optional[str] = Form(None),
    trade_date: Optional[str] = Form(None),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Upload and parse FpML confirmation file(s).
    
    Accepts single XML file or ZIP archive containing multiple FpML documents.
    Returns parsed canonical trades and validation results.
    """
    try:
        logger.info(f"Processing FpML upload: {file.filename}")
        
        # Validate file type
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in ['.xml', '.zip']:
            raise HTTPException(
                status_code=400, 
                detail="Only XML and ZIP files are supported"
            )
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Parse FpML file
            parser = FpMLParser()
            canonical_trades = parser.parse_file(temp_file_path)
            
            if not canonical_trades:
                raise HTTPException(
                    status_code=400,
                    detail="No valid trades found in FpML file"
                )
            
            # Store source file record
            file_service = FileService(db)
            source_file = file_service.create_source_file(
                filename=file.filename,
                file_kind=FileKind.FPML_CONFIRM,
                file_size=len(content),
                content_hash=file_service.calculate_hash(content)
            )
            
            # Update trades with source file reference
            for trade in canonical_trades:
                trade.source_file = file.filename
            
            # Prepare response
            response = {
                "file_id": source_file.id,
                "filename": file.filename,
                "file_size": len(content),
                "trades_parsed": len(canonical_trades),
                "trades": [_trade_to_response_dict(trade) for trade in canonical_trades],
                "parsing_summary": _generate_parsing_summary(canonical_trades),
                "validation_results": _validate_trades(canonical_trades)
            }
            
            logger.info(f"Successfully parsed {len(canonical_trades)} trades from {file.filename}")
            return response
            
        finally:
            # Clean up temporary file
            os.unlink(temp_file_path)
            
    except FpMLValidationError as e:
        logger.error(f"FpML validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing FpML file: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/otc/reconcile")
async def reconcile_otc_trades(
    internal_file: UploadFile = File(...),
    external_file: UploadFile = File(...),
    rate_tolerance_bp: float = Form(0.5),
    notional_tolerance: float = Form(1.0),
    date_tolerance_days: int = Form(0),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Reconcile internal OTC trades against external FpML confirmations.
    
    Performs economic matching with configurable tolerances and returns
    detailed break analysis.
    """
    try:
        logger.info(f"Reconciling OTC trades: {internal_file.filename} vs {external_file.filename}")
        
        # Parse internal trades (assume CSV format)
        internal_trades = await _parse_internal_trades(internal_file)
        
        # Parse external FpML confirmations
        external_trades = await _parse_external_fpml(external_file)
        
        if not internal_trades:
            raise HTTPException(status_code=400, detail="No internal trades found")
        
        if not external_trades:
            raise HTTPException(status_code=400, detail="No external confirmations found")
        
        # Configure reconciliation tolerances
        tolerance_config = OTCToleranceConfig(
            rate_tolerance_bp=rate_tolerance_bp,
            notional_tolerance=notional_tolerance,
            date_tolerance_days=date_tolerance_days
        )
        
        # Perform reconciliation
        recon_engine = OTCReconEngine(tolerance_config)
        recon_result = recon_engine.reconcile_trades(internal_trades, external_trades)
        
        # Store reconciliation run
        # TODO: Store in database for audit trail
        
        response = {
            "reconciliation_summary": {
                "internal_trades": recon_result.total_internal,
                "external_confirmations": recon_result.total_external,
                "matched_trades": recon_result.matched_count,
                "exceptions": recon_result.exception_count,
                "match_rate": f"{(recon_result.matched_count / max(recon_result.total_internal, 1)) * 100:.1f}%"
            },
            "tolerance_config": {
                "rate_tolerance_bp": rate_tolerance_bp,
                "notional_tolerance": notional_tolerance,
                "date_tolerance_days": date_tolerance_days
            },
            "exceptions": [_exception_to_response_dict(exc) for exc in recon_result.exceptions],
            "summary_stats": recon_result.summary_stats
        }
        
        logger.info(f"OTC reconciliation complete: {recon_result.matched_count} matches, {recon_result.exception_count} exceptions")
        return response
        
    except Exception as e:
        logger.error(f"Error in OTC reconciliation: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/otc/trades/{trade_id}")
async def get_otc_trade_details(
    trade_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get detailed information for specific OTC trade."""
    try:
        # TODO: Implement trade lookup from database
        # For now, return placeholder
        return {
            "trade_id": trade_id,
            "status": "not_implemented",
            "message": "Trade detail lookup not yet implemented"
        }
        
    except Exception as e:
        logger.error(f"Error getting trade details: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/otc/validation-rules")
async def get_validation_rules() -> Dict[str, Any]:
    """Get OTC trade validation rules and business logic."""
    try:
        return {
            "irs_rules": {
                "required_fields": [
                    "trade_id", "trade_date", "counterparty", "effective_date",
                    "maturity_date", "notional", "currency", "fixed_rate",
                    "floating_index", "pay_receive"
                ],
                "business_rules": [
                    "Maturity date must be after effective date",
                    "Trade date must be before or equal to effective date",
                    "Fixed rate must be between -1% and 20%",
                    "Notional must be positive"
                ],
                "tolerances": {
                    "fixed_rate": "0.5 basis points",
                    "notional": "1 unit",
                    "dates": "0 days (exact match)"
                }
            },
            "fx_forward_rules": {
                "required_fields": [
                    "trade_id", "trade_date", "counterparty", "value_date",
                    "currency1", "currency2", "notional1", "notional2", "forward_rate"
                ],
                "business_rules": [
                    "Value date must be after trade date",
                    "Currency1 and Currency2 must be different",
                    "Forward rate must be positive",
                    "Notional amounts must be consistent with rate"
                ],
                "tolerances": {
                    "forward_rate": "0.5 basis points",
                    "notional": "1 unit",
                    "dates": "0 days (exact match)"
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting validation rules: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


async def _parse_internal_trades(file: UploadFile) -> List[CanonicalTrade]:
    """Parse internal trades from CSV file."""
    # TODO: Implement CSV parsing for internal trades
    # For now, return empty list
    logger.warning("Internal trade parsing not yet implemented")
    return []


async def _parse_external_fpml(file: UploadFile) -> List[CanonicalTrade]:
    """Parse external FpML confirmations."""
    try:
        content = await file.read()
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xml') as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            parser = FpMLParser()
            return parser.parse_file(temp_file_path)
        finally:
            os.unlink(temp_file_path)
            
    except Exception as e:
        logger.error(f"Error parsing external FpML: {e}")
        raise


def _trade_to_response_dict(trade: CanonicalTrade) -> Dict[str, Any]:
    """Convert canonical trade to response dictionary."""
    return {
        "trade_id": trade.trade_id,
        "trade_date": trade.trade_date.isoformat() if trade.trade_date else None,
        "counterparty": trade.counterparty,
        "product_type": trade.product_type,
        "uti": trade.uti,
        "notional": float(trade.notional) if trade.notional else None,
        "currency": trade.currency,
        "effective_date": trade.effective_date.isoformat() if trade.effective_date else None,
        "maturity_date": trade.maturity_date.isoformat() if trade.maturity_date else None,
        "fixed_rate": float(trade.fixed_rate) if trade.fixed_rate else None,
        "floating_index": trade.floating_index,
        "pay_receive": trade.pay_receive,
        "currency1": trade.currency1,
        "currency2": trade.currency2,
        "forward_rate": float(trade.forward_rate) if trade.forward_rate else None,
        "value_date": trade.value_date.isoformat() if trade.value_date else None
    }


def _generate_parsing_summary(trades: List[CanonicalTrade]) -> Dict[str, Any]:
    """Generate summary of parsed trades."""
    irs_count = len([t for t in trades if t.product_type == "IRS"])
    fx_count = len([t for t in trades if t.product_type == "FX_FWD"])
    
    currencies = set()
    counterparties = set()
    
    for trade in trades:
        if trade.currency:
            currencies.add(trade.currency)
        if trade.currency1:
            currencies.add(trade.currency1)
        if trade.currency2:
            currencies.add(trade.currency2)
        counterparties.add(trade.counterparty)
    
    return {
        "total_trades": len(trades),
        "irs_trades": irs_count,
        "fx_forward_trades": fx_count,
        "unique_counterparties": len(counterparties),
        "currencies_involved": sorted(list(currencies)),
        "has_uti": len([t for t in trades if t.uti])
    }


def _validate_trades(trades: List[CanonicalTrade]) -> Dict[str, Any]:
    """Validate parsed trades against business rules."""
    validation_results = {
        "valid_trades": 0,
        "warnings": [],
        "errors": []
    }
    
    for trade in trades:
        try:
            # Basic validation
            if not trade.trade_id:
                validation_results["errors"].append(f"Missing trade ID")
                continue
            
            if not trade.counterparty:
                validation_results["warnings"].append(f"Trade {trade.trade_id}: Missing counterparty")
            
            # Product-specific validation
            if trade.product_type == "IRS":
                if trade.maturity_date and trade.effective_date:
                    if trade.maturity_date <= trade.effective_date:
                        validation_results["errors"].append(
                            f"Trade {trade.trade_id}: Maturity date must be after effective date"
                        )
                
                if trade.fixed_rate and (trade.fixed_rate < -0.01 or trade.fixed_rate > 0.20):
                    validation_results["warnings"].append(
                        f"Trade {trade.trade_id}: Fixed rate {trade.fixed_rate:.4f} seems unusual"
                    )
            
            elif trade.product_type == "FX_FWD":
                if trade.currency1 == trade.currency2:
                    validation_results["errors"].append(
                        f"Trade {trade.trade_id}: Currency1 and Currency2 cannot be the same"
                    )
                
                if trade.value_date and trade.trade_date:
                    if trade.value_date <= trade.trade_date:
                        validation_results["errors"].append(
                            f"Trade {trade.trade_id}: Value date must be after trade date"
                        )
            
            validation_results["valid_trades"] += 1
            
        except Exception as e:
            validation_results["errors"].append(f"Trade {trade.trade_id}: Validation error - {e}")
    
    return validation_results


def _exception_to_response_dict(exception) -> Dict[str, Any]:
    """Convert reconciliation exception to response dictionary."""
    return {
        "exception_type": exception.exception_type.value if hasattr(exception.exception_type, 'value') else str(exception.exception_type),
        "trade_id": exception.trade_id,
        "account": exception.account,
        "symbol": exception.symbol,
        "side": exception.side,
        "internal_qty": exception.internal_qty,
        "external_qty": exception.external_qty,
        "internal_price": exception.internal_price,
        "external_price": exception.external_price,
        "difference_summary": exception.difference_summary,
        "additional_details": getattr(exception, 'additional_details', {})
    }
