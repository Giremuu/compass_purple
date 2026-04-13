from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Source

router = APIRouter()

VALID_CATEGORIES = ("red", "blue", "purple", "utility")


class SourceCreate(BaseModel):
    name: str
    url: str
    description: str = ""
    category: str


@router.get("/")
def list_sources(db: Session = Depends(get_db)):
    """Return all sources grouped by category."""
    sources = db.query(Source).order_by(Source.category, Source.name).all()
    grouped: dict[str, list] = {}
    for s in sources:
        grouped.setdefault(s.category, []).append(
            {"id": s.id, "name": s.name, "url": s.url, "description": s.description}
        )
    return grouped


@router.post("/")
def add_source(body: SourceCreate, db: Session = Depends(get_db)):
    """Add a new external source."""
    if body.category not in VALID_CATEGORIES:
        raise HTTPException(status_code=400, detail="Invalid category")
    source = Source(**body.model_dump())
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


@router.delete("/{source_id}")
def delete_source(source_id: int, db: Session = Depends(get_db)):
    """Remove a source by ID."""
    source = db.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    db.delete(source)
    db.commit()
    return {"deleted": source_id}
