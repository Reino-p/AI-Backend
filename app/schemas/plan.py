from pydantic import BaseModel
from typing import List, Optional

class Task(BaseModel):
    title: str
    type: str
    est_minutes: int
    due_date: str
    resource_ref: Optional[str] = None

class PlanResponse(BaseModel):
    milestones: List[str]
    tasks: List[Task]