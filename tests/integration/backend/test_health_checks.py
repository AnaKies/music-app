from fastapi.testclient import TestClient

from backend.main import app


def test_health_check_reports_api_ok():
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_worker_health_check_reports_inline_mvp_runtime():
    with TestClient(app) as client:
        response = client.get("/health/worker")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "runtime": "inline_mvp",
        "workerMode": "api-process-inline",
        "safeSummary": "The MVP worker path is available through the API process.",
    }


def test_worker_health_check_reports_failed_separate_runtime(monkeypatch):
    monkeypatch.setenv("WORKER_RUNTIME_MODE", "separate")
    monkeypatch.setenv("WORKER_LIVENESS_STATUS", "absent")

    with TestClient(app) as client:
        response = client.get("/health/worker")

    assert response.status_code == 503
    assert response.json() == {
        "status": "failed",
        "runtime": "separate",
        "workerMode": "separate-worker-runtime",
        "safeSummary": "The expected worker runtime did not respond to the liveness check.",
    }


def test_worker_health_check_reports_healthy_separate_runtime_from_heartbeat(monkeypatch, tmp_path):
    heartbeat_file = tmp_path / "heartbeat"
    heartbeat_file.write_text("2026-03-20T21:00:00Z")

    monkeypatch.setenv("WORKER_RUNTIME_MODE", "separate")
    monkeypatch.delenv("WORKER_LIVENESS_STATUS", raising=False)
    monkeypatch.setenv("WORKER_HEARTBEAT_FILE", str(heartbeat_file))
    monkeypatch.setenv("WORKER_HEARTBEAT_TTL_SECONDS", "60")

    with TestClient(app) as client:
        response = client.get("/health/worker")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "runtime": "separate",
        "workerMode": "separate-worker-runtime",
        "safeSummary": "The worker runtime responded to the current liveness check.",
    }
