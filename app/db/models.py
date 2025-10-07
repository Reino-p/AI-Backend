from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Column, Relationship
from pgvector.sqlalchemy import Vector

#User entity
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    password_hash: str
    created_at: datetime = Field(default_factory=datetime.now)

#Content seeding test entity
class Content(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    text: str
    tags: str = Field(default="")
    embedding: List[float] | None = Field(
        default=None,
        sa_column=Column(Vector(768))
    )
    created_at: datetime = Field(default_factory=datetime.now)

#plans entities
class Plan(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    goal: str
    level: str
    minutes: int
    deadline: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # children
    milestones: List["PlanMilestone"] = Relationship(back_populates="plan", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    tasks: List["PlanTask"] = Relationship(back_populates="plan", sa_relationship_kwargs={"cascade": "all, delete-orphan"})

class PlanMilestone(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    plan_id: int = Field(foreign_key="plan.id", index=True)
    order_index: int
    text: str

    plan: Optional[Plan] = Relationship(back_populates="milestones")

class PlanTask(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    plan_id: int = Field(foreign_key="plan.id", index=True)
    order_index: int
    title: str
    type: str
    est_minutes: int
    due_date: str
    resource_ref: Optional[str] = None

    plan: Optional[Plan] = Relationship(back_populates="tasks")