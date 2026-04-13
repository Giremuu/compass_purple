from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Target

router = APIRouter()


class TargetCreate(BaseModel):
    name: str
    host: str
    port: int = 22
    username: str
    password: str = ""
    ssh_key_path: str = ""
    os: str = "linux"
    notes: str = ""


class TargetUpdate(BaseModel):
    name: str | None = None
    host: str | None = None
    port: int | None = None
    username: str | None = None
    password: str | None = None
    ssh_key_path: str | None = None
    os: str | None = None
    notes: str | None = None


def _serialize(target: Target) -> dict:
    return {
        "id": target.id,
        "name": target.name,
        "host": target.host,
        "port": target.port,
        "username": target.username,
        "os": target.os,
        "notes": target.notes,
        "created_at": target.created_at,
        # never return credentials in responses
    }


@router.get("/")
def list_targets(db: Session = Depends(get_db)):
    return [_serialize(t) for t in db.query(Target).all()]


@router.post("/")
def create_target(body: TargetCreate, db: Session = Depends(get_db)):
    target = Target(**body.model_dump())
    db.add(target)
    db.commit()
    db.refresh(target)
    return _serialize(target)


@router.get("/{target_id}")
def get_target(target_id: int, db: Session = Depends(get_db)):
    target = db.get(Target, target_id)
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    return _serialize(target)


@router.patch("/{target_id}")
def update_target(target_id: int, body: TargetUpdate, db: Session = Depends(get_db)):
    target = db.get(Target, target_id)
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(target, field, value)
    db.commit()
    db.refresh(target)
    return _serialize(target)


@router.delete("/{target_id}")
def delete_target(target_id: int, db: Session = Depends(get_db)):
    target = db.get(Target, target_id)
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    db.delete(target)
    db.commit()
    return {"deleted": target_id}
