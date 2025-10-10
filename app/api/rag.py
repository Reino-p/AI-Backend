from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text as sqltext
from sqlmodel import Session, select
from app.db.session import get_session
from app.db.models import Document, Chunk
from app.schemas.rag import IngestRequest, IngestResponse, SearchRequest, SearchResponse, SearchHit
from app.services.chunking import split_into_chunks
from app.services.embeddings import embed_text

router = APIRouter(tags=["rag"])

@router.post("/content/ingest", response_model=IngestResponse)
async def ingest(body: IngestRequest, s: Session = Depends(get_session)):
    if not body.text.strip():
        raise HTTPException(400, "Empty text")

    doc = Document(title=body.title.strip(), tags=body.tags)
    s.add(doc)
    s.flush()

    parts = [p for p in split_into_chunks(body.text) if p.strip()]
    if not parts:
        raise HTTPException(400, "No non-empty chunks after splitting")

    for i, chunk_text in enumerate(parts, start=1):
        emb = await embed_text(chunk_text)  # will raise if empty/mismatched
        s.add(Chunk(document_id=doc.id, order_index=i, text=chunk_text, embedding=emb, meta=None))

    s.commit()
    return IngestResponse(document_id=doc.id, chunks=len(parts))

@router.post("/rag/search", response_model=SearchResponse)
async def rag_search(body: SearchRequest, s: Session = Depends(get_session)):
    q = (body.query or "").strip()
    if not q:
        return SearchResponse(hits=[])

    qvec = await embed_text(q)  # validated vector (length == EMBED_DIM)

    # use pgvector comparator so the param is typed as 'vector'
    dist = Chunk.embedding.cosine_distance(qvec)

    stmt = (
        select(
            Chunk.id,
            Chunk.document_id,
            Chunk.text,
            Document.title,
            dist.label("score"),
        )
        .join(Document, Document.id == Chunk.document_id)
        .order_by(dist)
        .limit(body.top_k)
    )

    rows = s.exec(stmt).all()

    hits = [
        SearchHit(
            id=row[0],
            document_id=row[1],
            chunk=row[2],
            title=row[3],
            score=float(row[4]),
        )
        for row in rows
    ]
    return SearchResponse(hits=hits)