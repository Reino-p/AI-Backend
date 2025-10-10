from sqlalchemy import text
from sqlmodel import SQLModel, create_engine, Session
from app.core.config import DATABASE_URL

engine = create_engine(DATABASE_URL, echo=False)

def init_db() -> None:
    # Create all tables from models
    SQLModel.metadata.create_all(engine)

    # Ensure pgvector index exists
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_chunk_embedding_cosine
            ON chunk
            USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 100);
        """))
        conn.commit()
        print("pgvector IVFFlat index ensured.")

def get_session():
    with Session(engine) as session:
        yield session