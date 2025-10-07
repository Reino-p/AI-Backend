from typing import List, Optional
from pydantic import BaseModel, Field

class PlanItemTaskIn(BaseModel):
    title: str
    type: str
    est_minutes: int = Field(ge=5, le=240)
    due_date: str
    resource_ref: Optional[str] = None

class PlanCreate(BaseModel):
    name: str
    goal: str
    level: str
    minutes: int
    deadline: str
    milestones: List[str]
    tasks: List[PlanItemTaskIn]

class PlanSummary(BaseModel):
    id: int
    name: str

class PlanTaskOut(PlanItemTaskIn):
    id: int
    order_index: int

class PlanMilestoneOut(BaseModel):
    id: int
    order_index: int
    text: str

class PlanRead(BaseModel):
    id: int
    name: str
    goal: str
    level: str
    minutes: int
    deadline: str
    milestones: List[PlanMilestoneOut]
    tasks: List[PlanTaskOut]