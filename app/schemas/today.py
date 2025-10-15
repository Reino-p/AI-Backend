from pydantic import BaseModel
from typing import Optional, List

class TodayTask(BaseModel):
    id: int
    title: str
    type: str
    est_minutes: int
    due_date: str
    resource_ref: Optional[str] = None

class TodayResponse(BaseModel):
    plan_id: int
    tasks: List[TodayTask]