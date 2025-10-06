from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import Session
from app.db.session import get_session
from app.db.models import Content

router = APIRouter(tags=["health"])

@router.get("/health")
def health():
    return {"status": "ok"}

class SeedIn(BaseModel):
    title: str = "Hello"
    text: str = "Just a seed row"
    tags: str = "test"

@router.post("/__seed")
def seed(body: SeedIn, s: Session = Depends(get_session)):
    item = Content(title=body.title, text=body.text, tags=body.tags)
    s.add(item); s.commit(); s.refresh(item)
    return {"id": item.id}