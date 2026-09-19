"""Optional read-only U-Port berth reference endpoint."""

import os
from pathlib import Path

from fastapi import APIRouter, HTTPException

from services.uport.operations.berth_reference import (
    BerthReferenceCollection, BerthReferenceError, load_berth_reference,
)

router = APIRouter(prefix="/uport/operations", tags=["U-Port Operations"])


@router.get("/berth-reference", response_model=BerthReferenceCollection)
def get_berth_reference() -> BerthReferenceCollection:
    """Return sourced berth metadata only when an operator configured a CSV."""

    configured = os.environ.get("UPORT_BERTH_SPEC_CSV")
    if not configured:
        raise HTTPException(status_code=503, detail={
            "code": "DATASET_NOT_AVAILABLE", "message": "Berth reference CSV is not configured",
        })
    try:
        return load_berth_reference(Path(configured))
    except BerthReferenceError as exc:
        raise HTTPException(status_code=503, detail={
            "code": "DATASET_NOT_AVAILABLE", "message": str(exc),
        }) from exc
