from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Column
from pgvector.sqlalchemy import Vector

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    password_hash: str
    created_at: datetime = Field(default_factory=datetime.now)

# 768 dims to match `nomic-embed-text`
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