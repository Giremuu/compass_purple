import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Run
from engine.loader import load_modules

router = APIRouter()

VALID_TYPES = ("red", "blue", "purple", "utility")


class RunRequest(BaseModel):
    params: dict = {}


@router.post("/{module_type}/{name}")
def run_module(module_type: str, name: str, body: RunRequest, db: Session = Depends(get_db)):
    """Execute a module, persist the result, and return it."""
    if module_type not in VALID_TYPES:
        raise HTTPException(status_code=404, detail="Unknown module type")
    modules = load_modules(module_type)
    if name not in modules:
        raise HTTPException(status_code=404, detail=f"Module '{name}' not found")

    result = modules[name].run(body.params)
    status = result.get("status", "success")

    run = Run(
        module_type=module_type,
        module_name=name,
        params=json.dumps(body.params),
        result=json.dumps(result),
        status=status,
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    return {"id": run.id, "module": name, "type": module_type, "result": result}


@router.get("/")
def list_runs(db: Session = Depends(get_db)):
    """Return the full run history, most recent first."""
    runs = db.query(Run).order_by(Run.created_at.desc()).all()
    return [
        {
            "id": r.id,
            "module_type": r.module_type,
            "module_name": r.module_name,
            "status": r.status,
            "created_at": r.created_at,
            "result": r.result_dict(),
        }
        for r in runs
    ]
