from io import BytesIO

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.database import Base, engine, get_db
from backend.domain.cases.models import TranspositionCase
from backend.domain.scores.models import ScoreDocument  # noqa: F401
from backend.main import app


def _reset_tables() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def _override_get_db(session: Session):
    def _dependency():
        try:
            yield session
        finally:
            pass

    return _dependency


def _seed_case(session: Session, case_id: str, status: str) -> None:
    session.add(
        TranspositionCase(
            id=case_id,
            status=status,
            instrument_identity="flute",
            comfort_range_min="G3",
            comfort_range_max="D5",
        )
    )
    session.commit()


def test_post_scores_accepts_valid_musicxml_for_ready_case():
    _reset_tables()
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    _seed_case(session, "case-ready", "ready_for_upload")
    app.dependency_overrides[get_db] = _override_get_db(session)

    try:
      with TestClient(app) as client:
        response = client.post(
            "/scores",
            data={"transpositionCaseId": "case-ready"},
            files={"file": ("example.musicxml", BytesIO(b"<score-partwise version='4.0'></score-partwise>"), "application/xml")},
        )

      assert response.status_code == 202
      payload = response.json()
      assert payload["format"] == "musicxml"
      assert payload["acceptedStatus"] == "uploaded"
      assert payload["initialProcessingSnapshot"]["processingStatus"] == "uploaded"
      persisted_case = session.query(TranspositionCase).filter(TranspositionCase.id == "case-ready").first()
      assert persisted_case is not None
      assert persisted_case.score_count == 1
    finally:
      app.dependency_overrides.clear()
      transaction.rollback()
      session.close()
      connection.close()


def test_post_scores_rejects_non_ready_case():
    _reset_tables()
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    _seed_case(session, "case-not-ready", "interview_in_progress")
    app.dependency_overrides[get_db] = _override_get_db(session)

    try:
      with TestClient(app) as client:
        response = client.post(
            "/scores",
            data={"transpositionCaseId": "case-not-ready"},
            files={"file": ("example.musicxml", BytesIO(b"<score-partwise version='4.0'></score-partwise>"), "application/xml")},
        )

      assert response.status_code == 409
      assert response.json() == {
          "detail": "The selected case is not ready for score upload.",
      }
    finally:
      app.dependency_overrides.clear()
      transaction.rollback()
      session.close()
      connection.close()


def test_post_scores_rejects_unsupported_file_type():
    _reset_tables()
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    _seed_case(session, "case-ready", "ready_for_upload")
    app.dependency_overrides[get_db] = _override_get_db(session)

    try:
      with TestClient(app) as client:
        response = client.post(
            "/scores",
            data={"transpositionCaseId": "case-ready"},
            files={"file": ("example.pdf", BytesIO(b"%PDF-1.7"), "application/pdf")},
        )

      assert response.status_code == 415
      assert response.json() == {
          "detail": "Only MusicXML uploads are supported.",
      }
    finally:
      app.dependency_overrides.clear()
      transaction.rollback()
      session.close()
      connection.close()


def test_post_scores_rejects_oversized_upload():
    _reset_tables()
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    _seed_case(session, "case-ready", "ready_for_upload")
    app.dependency_overrides[get_db] = _override_get_db(session)

    try:
      with TestClient(app) as client:
        response = client.post(
            "/scores",
            data={"transpositionCaseId": "case-ready"},
            files={"file": ("example.musicxml", BytesIO(b"<score-partwise>" + (b"a" * (5 * 1024 * 1024 + 1))), "application/xml")},
        )

      assert response.status_code == 413
      assert response.json() == {
          "detail": "The uploaded file exceeds the maximum allowed size.",
      }
    finally:
      app.dependency_overrides.clear()
      transaction.rollback()
      session.close()
      connection.close()
