from fastapi import APIRouter, Depends
from sqlmodel import Session
from app.db.session import get_session
from app.db.models import Content

router = APIRouter(tags=["health"])

@router.get("/health")
def health():
    return {"status": "ok"}

# @router.post("/__seed")
# def seed(s: Session = Depends(get_session)):
#     item = Content(title="Hello", text="Just a seed row", tags="test")
#     s.add(item); s.commit(); s.refresh(item)
#     return {"id": item.id}