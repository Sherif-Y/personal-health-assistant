from sqlmodel import Session, SQLModel, create_engine

from app.config import settings

settings.database_path.parent.mkdir(parents=True, exist_ok=True)
engine = create_engine("sqlite:///{}".format(settings.database_path))


def create_db_and_tables():
    from app.db import models  # noqa: F401 (ensures tables are registered on SQLModel.metadata)

    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
