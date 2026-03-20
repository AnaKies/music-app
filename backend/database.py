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
    statements = []

    if "score_documents" in inspector.get_table_names():
        existing_columns = {column["name"] for column in inspector.get_columns("score_documents")}
        if "source_musicxml" not in existing_columns:
            statements.append("ALTER TABLE score_documents ADD COLUMN source_musicxml TEXT")

    if "transformation_jobs" in inspector.get_table_names():
        existing_columns = {column["name"] for column in inspector.get_columns("transformation_jobs")}
        if "result_storage_uri" not in existing_columns:
            statements.append("ALTER TABLE transformation_jobs ADD COLUMN result_storage_uri VARCHAR")
        if "result_filename" not in existing_columns:
            statements.append("ALTER TABLE transformation_jobs ADD COLUMN result_filename VARCHAR")
        if "result_revision_token" not in existing_columns:
            statements.append("ALTER TABLE transformation_jobs ADD COLUMN result_revision_token VARCHAR")
        if "exported_at" not in existing_columns:
            statements.append("ALTER TABLE transformation_jobs ADD COLUMN exported_at DATETIME")

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
