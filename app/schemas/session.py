from typing import Optional
from pydantic import BaseModel
from app.schemas.coach import Reflection

class StartSessionRequest(BaseModel):
    plan_id: int

class StartSessionResponse(BaseModel):
    id: int
    started_at: str

class EndSessionResponse(BaseModel):
    id: int
    ended_at: str

class CompleteTaskRequest(BaseModel):
    outcome: str   # 'done' | 'partial' | 'skipped'
    notes: Optional[str] = None
    rating: Optional[int] = None
    session_id: int | None = None
    reflection: Optional[Reflection] = None