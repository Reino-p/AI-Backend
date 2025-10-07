from pydantic import BaseModel, Field, field_validator
from typing import List, Optional

class PlanRequest(BaseModel):
    goal: str = Field(..., min_length=3)
    level: str = Field(default="beginner")
    minutes: int = Field(default=45, ge=10, le=240)
    deadline: str = Field(default="in 4 weeks")

class Task(BaseModel):
    title: str
    type: str
    est_minutes: int = Field(ge=5, le=240)
    due_date: str
    resource_ref: Optional[str] = None

class PlanResponse(BaseModel):
    milestones: List[str]
    tasks: List[Task]

    @field_validator("milestones")
    @classmethod
    def non_empty_milestones(cls, v):
        if not v: raise ValueError("at least one milestone is required")
        return v