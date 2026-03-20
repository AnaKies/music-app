from dataclasses import dataclass
from typing import Dict, List, Optional
from xml.etree import ElementTree

from backend.api.schemas.scores import ParseFailureType

CANONICAL_SCORE_SCHEMA_VERSION = "v1"


@dataclass
class CanonicalScorePayload:
    schema_version: str
    title: Optional[str]
    parts: List[Dict[str, str]]
    measure_count: int
    note_count: int
    rest_count: int


@dataclass
class ParseFailurePayload:
    failure_type: ParseFailureType


@dataclass
class ParseScoreResult:
    canonical_score: Optional[CanonicalScorePayload] = None
    failure: Optional[ParseFailurePayload] = None


def _local_name(tag: str) -> str:
    if "}" in tag:
        return tag.rsplit("}", 1)[1]
    return tag


def parse_musicxml(content: bytes) -> ParseScoreResult:
    try:
        root = ElementTree.fromstring(content)
    except ElementTree.ParseError:
        return ParseScoreResult(
            failure=ParseFailurePayload(failure_type=ParseFailureType.INVALID_XML),
        )

    if _local_name(root.tag) not in {"score-partwise", "score-timewise"}:
        return ParseScoreResult(
            failure=ParseFailurePayload(failure_type=ParseFailureType.UNSUPPORTED_STRUCTURE),
        )

    title = _read_title(root)
    parts = _read_parts(root)
    measures = root.findall(".//{*}part/{*}measure")
    notes = root.findall(".//{*}note")
    pitched_notes = [note for note in notes if note.find("{*}pitch") is not None]
    rests = [note for note in notes if note.find("{*}rest") is not None]

    if not parts or not measures or (not pitched_notes and not rests):
        return ParseScoreResult(
            failure=ParseFailurePayload(failure_type=ParseFailureType.EMPTY_SCORE),
        )

    return ParseScoreResult(
        canonical_score=CanonicalScorePayload(
            schema_version=CANONICAL_SCORE_SCHEMA_VERSION,
            title=title,
            parts=parts,
            measure_count=len(measures),
            note_count=len(pitched_notes),
            rest_count=len(rests),
        ),
    )


def _read_title(root: ElementTree.Element) -> Optional[str]:
    for candidate in (
        root.find(".//{*}work-title"),
        root.find(".//{*}movement-title"),
    ):
        if candidate is not None and candidate.text:
            value = candidate.text.strip()
            if value:
                return value
    return None


def _read_parts(root: ElementTree.Element) -> List[Dict[str, str]]:
    parts: List[Dict[str, str]] = []
    for score_part in root.findall(".//{*}part-list/{*}score-part"):
        part_id = (score_part.attrib.get("id") or "").strip()
        name_node = score_part.find("{*}part-name")
        name = (name_node.text or "").strip() if name_node is not None and name_node.text else ""
        if part_id:
            parts.append(
                {
                    "id": part_id,
                    "name": name or f"Part {part_id}",
                }
            )
    return parts
