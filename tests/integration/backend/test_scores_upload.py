from io import BytesIO
from zipfile import ZipFile

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.database import Base, engine, get_db
from backend.domain.cases.models import TranspositionCase
from backend.domain.scores.models import CanonicalScore, ScoreDocument
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
            files={
                "file": (
                    "example.musicxml",
                    BytesIO(
                        b"""
                        <score-partwise version='4.0'>
                          <part-list>
                            <score-part id='P1'><part-name>Flute</part-name></score-part>
                          </part-list>
                          <part id='P1'>
                            <measure number='1'>
                              <note><rest/><duration>4</duration></note>
                            </measure>
                          </part>
                        </score-partwise>
                        """
                    ),
                    "application/xml",
                )
            },
        )

      assert response.status_code == 202
      payload = response.json()
      assert payload["format"] == "musicxml"
      assert payload["acceptedStatus"] == "parsed"
      assert payload["initialProcessingSnapshot"]["processingStatus"] == "parsed"
      assert payload["initialProcessingSnapshot"]["canonicalScoreSummary"] == {
          "schemaVersion": "v1",
          "title": None,
          "partCount": 1,
          "measureCount": 1,
          "noteCount": 0,
          "restCount": 1,
          "parts": [{"partId": "P1", "name": "Flute"}],
      }
      persisted_case = session.query(TranspositionCase).filter(TranspositionCase.id == "case-ready").first()
      persisted_score = session.query(ScoreDocument).filter(ScoreDocument.id == payload["scoreDocumentId"]).first()
      persisted_canonical = session.query(CanonicalScore).filter(CanonicalScore.score_document_id == payload["scoreDocumentId"]).first()
      assert persisted_case is not None
      assert persisted_score is not None
      assert persisted_score.processing_status.value == "parsed"
      assert persisted_score.parse_failure_type is None
      assert persisted_canonical is not None
      assert persisted_canonical.parts == [{"id": "P1", "name": "Flute"}]
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
          "detail": "Only MusicXML-family uploads (.musicxml, .xml, .mxl) are supported.",
      }
    finally:
      app.dependency_overrides.clear()
      transaction.rollback()
      session.close()
      connection.close()


def test_post_scores_accepts_valid_xml_upload_for_ready_case():
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
            files={
                "file": (
                    "example.xml",
                    BytesIO(
                        b"""<?xml version='1.0' encoding='UTF-8'?>
                        <score-partwise version='4.0'>
                          <part-list>
                            <score-part id='P1'><part-name>Flute</part-name></score-part>
                          </part-list>
                          <part id='P1'>
                            <measure number='1'>
                              <note><pitch><step>C</step><octave>4</octave></pitch><duration>4</duration></note>
                            </measure>
                          </part>
                        </score-partwise>
                        """
                    ),
                    "application/xml",
                )
            },
        )

      assert response.status_code == 202
      assert response.json()["acceptedStatus"] == "parsed"
    finally:
      app.dependency_overrides.clear()
      transaction.rollback()
      session.close()
      connection.close()


def test_post_scores_accepts_valid_mxl_upload_for_ready_case():
    _reset_tables()
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    _seed_case(session, "case-ready", "ready_for_upload")
    app.dependency_overrides[get_db] = _override_get_db(session)

    archive_bytes = BytesIO()
    with ZipFile(archive_bytes, "w") as archive:
        archive.writestr(
            "score.musicxml",
            """<?xml version='1.0' encoding='UTF-8'?>
            <score-partwise version='4.0'>
              <part-list>
                <score-part id='P1'><part-name>Flute</part-name></score-part>
              </part-list>
              <part id='P1'>
                <measure number='1'>
                  <note><rest/><duration>4</duration></note>
                </measure>
              </part>
            </score-partwise>
            """,
        )

    try:
      with TestClient(app) as client:
        response = client.post(
            "/scores",
            data={"transpositionCaseId": "case-ready"},
            files={
                "file": (
                    "example.mxl",
                    BytesIO(archive_bytes.getvalue()),
                    "application/vnd.recordare.musicxml",
                )
            },
        )

      assert response.status_code == 202
      payload = response.json()
      assert payload["acceptedStatus"] == "parsed"
      assert payload["initialProcessingSnapshot"]["processingStatus"] == "parsed"
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


def test_post_scores_persists_typed_parse_failure_for_malformed_musicxml():
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
            files={
                "file": (
                    "broken.musicxml",
                    BytesIO(b"<score-partwise version='4.0'><part-list><score-part id='P1'><part-name>Flute</part-name></score-part></part-list>"),
                    "application/xml",
                )
            },
        )

      assert response.status_code == 202
      payload = response.json()
      assert payload["acceptedStatus"] == "parse_failed"
      assert payload["initialProcessingSnapshot"]["processingStatus"] == "parse_failed"
      assert payload["initialProcessingSnapshot"]["parseFailureType"] == "invalid_xml"
      assert payload["initialProcessingSnapshot"]["canonicalScoreSummary"] is None

      persisted_score = session.query(ScoreDocument).filter(ScoreDocument.id == payload["scoreDocumentId"]).first()
      persisted_canonical = session.query(CanonicalScore).filter(CanonicalScore.score_document_id == payload["scoreDocumentId"]).first()
      assert persisted_score is not None
      assert persisted_score.processing_status.value == "parse_failed"
      assert persisted_score.parse_failure_type.value == "invalid_xml"
      assert persisted_canonical is None
    finally:
      app.dependency_overrides.clear()
      transaction.rollback()
      session.close()
      connection.close()
