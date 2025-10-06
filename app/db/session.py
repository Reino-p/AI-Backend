from sqlmodel import SQLModel, create_engine, Session
from app.core.config import DATABASE_URL

engine = create_engine(DATABASE_URL, echo=False)

def init_db() -> None:
    # create tables if models exist
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session