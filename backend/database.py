from sqlalchemy import create_engine, inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Für MVP-Zwecke verwenden wir SQLite lokal, falls keine Postgres-URL konfiguriert ist
SQLALCHEMY_DATABASE_URL = "sqlite:///./musicapp.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def run_startup_migrations() -> None:
    inspector = inspect(engine)
    if "score_documents" not in inspector.get_table_names():
        return

    existing_columns = {column["name"] for column in inspector.get_columns("score_documents")}
    statements = []

    if "source_musicxml" not in existing_columns:
        statements.append("ALTER TABLE score_documents ADD COLUMN source_musicxml TEXT")

    if not statements:
        return

    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
