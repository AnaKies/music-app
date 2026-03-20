from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from backend.api.schemas.scores import CanonicalScorePartSummary, CanonicalScoreSummary
from backend.services.shared.musicxml import ensure_xml_declaration
from backend.services.scores.parser import parse_musicxml


@dataclass
class ExportedTransformationArtifact:
    storage_uri: str
    revision_token: str
    filename: str
    exported_at: datetime
    canonical_summary: CanonicalScoreSummary


def export_transformation_result(
    *,
    transformation_job_id: str,
    transformed_musicxml: str,
    original_filename: str,
) -> ExportedTransformationArtifact:
    exported_at = datetime.now(timezone.utc)
    exported_musicxml = ensure_xml_declaration(transformed_musicxml)
    parse_result = parse_musicxml(exported_musicxml.encode("utf-8"))
    if parse_result.failure is not None or parse_result.canonical_score is None:
        raise ValueError("invalid_exported_musicxml")

    canonical_score = parse_result.canonical_score
    output_filename = _build_output_filename(original_filename)
    return ExportedTransformationArtifact(
        storage_uri=f"local://transformations/{transformation_job_id}/{output_filename}",
        revision_token=exported_at.isoformat(),
        filename=output_filename,
        exported_at=exported_at,
        canonical_summary=CanonicalScoreSummary(
            schemaVersion=canonical_score.schema_version,
            title=canonical_score.title,
            partCount=len(canonical_score.parts or []),
            measureCount=canonical_score.measure_count,
            noteCount=canonical_score.note_count,
            restCount=canonical_score.rest_count,
            parts=[
                CanonicalScorePartSummary(
                    partId=part.get("id", ""),
                    name=part.get("name", ""),
                )
                for part in (canonical_score.parts or [])
            ],
        ),
    )


def _build_output_filename(original_filename: str) -> str:
    stem = Path(original_filename).stem or "score"
    return f"{stem}-transformed.musicxml"
