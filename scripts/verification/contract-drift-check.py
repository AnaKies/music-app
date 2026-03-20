#!/usr/bin/env python3

import json
import os
import sys
import urllib.error
import urllib.request


def fetch_json(base_url: str, path: str) -> dict:
    url = f"{base_url.rstrip('/')}{path}"
    with urllib.request.urlopen(url) as response:
        return json.loads(response.read().decode("utf-8"))


def ensure_keys(payload: dict, required_keys: list[str], label: str) -> None:
    missing = [key for key in required_keys if key not in payload]
    if missing:
        raise AssertionError(f"{label} is missing keys: {', '.join(missing)}")


def compare_health(preview_api_base_url: str, production_api_base_url: str) -> None:
    preview_health = fetch_json(preview_api_base_url, "/health")
    production_health = fetch_json(production_api_base_url, "/health")
    if preview_health.get("status") != "ok" or production_health.get("status") != "ok":
        raise AssertionError("Health status must be 'ok' in both environments")


def compare_score_contract(preview_api_base_url: str, production_api_base_url: str, score_id: str) -> None:
    preview_score = fetch_json(preview_api_base_url, f"/scores/{score_id}")
    production_score = fetch_json(production_api_base_url, f"/scores/{score_id}")
    required_keys = ["id", "processingStatus", "sourcePreview", "resultPreview"]

    ensure_keys(preview_score, required_keys, "Preview score contract")
    ensure_keys(production_score, required_keys, "Production score contract")

    preview_status = preview_score["processingStatus"]
    production_status = production_score["processingStatus"]
    if preview_status != production_status:
        raise AssertionError(
            "Score processingStatus drift detected: "
            f"preview={preview_status}, production={production_status}"
        )


def compare_transformation_contract(
    preview_api_base_url: str, production_api_base_url: str, transformation_id: str
) -> None:
    preview_transformation = fetch_json(preview_api_base_url, f"/transformations/{transformation_id}")
    production_transformation = fetch_json(production_api_base_url, f"/transformations/{transformation_id}")
    required_keys = ["id", "status", "warnings", "safeSummary"]

    ensure_keys(preview_transformation, required_keys, "Preview transformation contract")
    ensure_keys(production_transformation, required_keys, "Production transformation contract")

    preview_status = preview_transformation["status"]
    production_status = production_transformation["status"]
    if preview_status != production_status:
        raise AssertionError(
            "Transformation status drift detected: "
            f"preview={preview_status}, production={production_status}"
        )


def main() -> int:
    preview_api_base_url = os.getenv("PREVIEW_API_BASE_URL", "").strip()
    production_api_base_url = os.getenv("PRODUCTION_API_BASE_URL", "").strip()
    score_id = os.getenv("SCORE_ID", "").strip()
    transformation_id = os.getenv("TRANSFORMATION_ID", "").strip()

    if not preview_api_base_url or not production_api_base_url:
        print("PREVIEW_API_BASE_URL and PRODUCTION_API_BASE_URL are required", file=sys.stderr)
        return 1

    if not score_id:
        print("SCORE_ID is required for the drift check", file=sys.stderr)
        return 1

    try:
        compare_health(preview_api_base_url, production_api_base_url)
        compare_score_contract(preview_api_base_url, production_api_base_url, score_id)
        if transformation_id:
            compare_transformation_contract(preview_api_base_url, production_api_base_url, transformation_id)
    except (AssertionError, urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError) as exc:
        print(f"Drift check failed: {exc}", file=sys.stderr)
        return 1

    print("Environment-state drift check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
