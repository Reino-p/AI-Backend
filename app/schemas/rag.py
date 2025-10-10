from typing import List, Optional
from pydantic import BaseModel, Field

class IngestRequest(BaseModel):
    title: str
    text: str
    tags: Optional[str] = None

class IngestResponse(BaseModel):
    document_id: int
    chunks: int

class SearchRequest(BaseModel):
    query: str
    top_k: int = Field(default=6, ge=1, le=20)

class SearchHit(BaseModel):
    id: int
    document_id: int
    title: str
    chunk: str
    score: float  # cosine distance (lower = closer)

class SearchResponse(BaseModel):
    hits: List[SearchHit]