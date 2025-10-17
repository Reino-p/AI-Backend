from pydantic import BaseModel, Field
from typing import Literal, Optional, List

class Reflection(BaseModel):
    confidence: int = Field(ge=1, le=5)
    blockers: Optional[str] = None
    took_minutes: Optional[int] = Field(default=None, ge=1, le=600)
    want_more_practice: bool = False

# actions the coach can take
class CoachAction(BaseModel):
    type: Literal["add_task", "reschedule_task", "tip"]
    # add_task
    title: Optional[str] = None
    est_minutes: Optional[int] = None
    due_in_days: Optional[int] = None
    resource_ref: Optional[str] = None
    # reschedule_task
    target_task_id: Optional[int] = None
    push_days: Optional[int] = None
    # tip
    tip: Optional[str] = None

class CoachDecision(BaseModel):
    actions: List[CoachAction] = []