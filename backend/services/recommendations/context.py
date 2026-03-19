from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.api.schemas.recommendations import (
    ConfirmedCaseConstraints,
    InferredConstraintAdvisory,
    InstrumentKnowledge,
    RecommendationContext,
    RecommendationScoreSummary,
)
from backend.domain.cases.models import TranspositionCase
from backend.domain.interviews.models import InterviewSession
from backend.domain.scores.models import ScoreDocument

CONTEXT_VERSION = "v1"

INSTRUMENT_KNOWLEDGE = {
    "flute": {
        "display_name": "Flute",
        "transposition": "concert_c",
        "written_range_min": "C4",
        "written_range_max": "D7",
        "preferred_clefs": ["treble"],
        "key_suitability_notes": ["Agile in sharp keys", "Extended upper register needs care"],
    },
    "trumpet-bb": {
        "display_name": "B-flat Trumpet",
        "transposition": "bb_up_major_second",
        "written_range_min": "F#3",
        "written_range_max": "C6",
        "preferred_clefs": ["treble"],
        "key_suitability_notes": ["Sustained high tessitura is tiring", "Concert flat keys can add reading load"],
    },
    "clarinet-bb": {
        "display_name": "B-flat Clarinet",
        "transposition": "bb_up_major_second",
        "written_range_min": "E3",
        "written_range_max": "C7",
        "preferred_clefs": ["treble"],
        "key_suitability_notes": ["Break crossing affects fingering continuity"],
    },
    "alto-sax-eb": {
        "display_name": "E-flat Alto Saxophone",
        "transposition": "eb_down_major_sixth",
        "written_range_min": "Bb3",
        "written_range_max": "F6",
        "preferred_clefs": ["treble"],
        "key_suitability_notes": ["Upper register endurance varies by player"],
    },
    "horn-f": {
        "display_name": "F Horn",
        "transposition": "f_up_perfect_fifth",
        "written_range_min": "B2",
        "written_range_max": "F5",
        "preferred_clefs": ["treble", "bass"],
        "key_suitability_notes": ["High sustained writing needs conservative targeting"],
    },
}


def build_recommendation_context(
    db: Session,
    transposition_case_id: str,
    score_document_id: str,
) -> RecommendationContext:
    case = db.query(TranspositionCase).filter(TranspositionCase.id == transposition_case_id).first()
    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case with id {transposition_case_id} not found.",
        )

    score_document = db.query(ScoreDocument).filter(ScoreDocument.id == score_document_id).first()
    if score_document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Score document with id {score_document_id} not found.",
        )

    if score_document.transposition_case_id != transposition_case_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The selected score document does not belong to the selected case.",
        )

    if score_document.canonical_score is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The selected score is not available in canonical form.",
        )

    knowledge = _instrument_knowledge_for(case.instrument_identity)
    inferred_constraints = _build_inferred_advisory(db, transposition_case_id)

    return RecommendationContext(
        contextVersion=CONTEXT_VERSION,
        transpositionCaseId=transposition_case_id,
        scoreDocumentId=score_document_id,
        confirmedConstraints=ConfirmedCaseConstraints(
            instrumentIdentity=case.instrument_identity,
            highestPlayableTone=case.highest_playable_tone,
            lowestPlayableTone=case.lowest_playable_tone,
            restrictedTones=case.restricted_tones or [],
            restrictedRegisters=case.restricted_registers or [],
            difficultKeys=case.difficult_keys or [],
            preferredKeys=case.preferred_keys or [],
            comfortRangeMin=case.comfort_range_min,
            comfortRangeMax=case.comfort_range_max,
        ),
        inferredConstraints=inferred_constraints,
        instrumentKnowledge=knowledge,
        scoreSummary=RecommendationScoreSummary(
            schemaVersion=score_document.canonical_score.schema_version,
            title=score_document.canonical_score.title,
            partCount=len(score_document.canonical_score.parts or []),
            measureCount=score_document.canonical_score.measure_count,
            noteCount=score_document.canonical_score.note_count,
            restCount=score_document.canonical_score.rest_count,
            partNames=[part.get("name", "") for part in (score_document.canonical_score.parts or [])],
        ),
    )


def _instrument_knowledge_for(instrument_identity: str) -> InstrumentKnowledge:
    knowledge = INSTRUMENT_KNOWLEDGE.get(instrument_identity)
    if knowledge is None:
        return InstrumentKnowledge(
            instrumentIdentity=instrument_identity,
            displayName=instrument_identity,
            transposition="unknown",
            writtenRangeMin="unknown",
            writtenRangeMax="unknown",
            preferredClefs=[],
            keySuitabilityNotes=["No curated instrument knowledge is available yet."],
        )

    return InstrumentKnowledge(
        instrumentIdentity=instrument_identity,
        displayName=knowledge["display_name"],
        transposition=knowledge["transposition"],
        writtenRangeMin=knowledge["written_range_min"],
        writtenRangeMax=knowledge["written_range_max"],
        preferredClefs=knowledge["preferred_clefs"],
        keySuitabilityNotes=knowledge["key_suitability_notes"],
    )


def _build_inferred_advisory(db: Session, transposition_case_id: str) -> Optional[InferredConstraintAdvisory]:
    latest_session = (
        db.query(InterviewSession)
        .filter(InterviewSession.case_id == transposition_case_id)
        .order_by(InterviewSession.updated_at.desc())
        .first()
    )
    if latest_session is None:
        return None

    advisory_notes = []
    for answer in latest_session.answers or []:
        if answer.get("lowConfidenceFlag") and answer.get("value", {}).get("text"):
            advisory_notes.append(answer["value"]["text"])

    follow_up_reason = (latest_session.low_confidence or {}).get("reason")
    if follow_up_reason:
        advisory_notes.append(str(follow_up_reason))

    if not advisory_notes:
        return None

    return InferredConstraintAdvisory(
        source="interview_low_confidence",
        confidence="low",
        advisoryNotes=advisory_notes,
    )
