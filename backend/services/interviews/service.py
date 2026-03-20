from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.api.schemas.cases import CaseStatus
from backend.api.schemas.interviews import (
    InterviewAdvanceRequest,
    InterviewAdvanceResponse,
    InterviewAnswerValue,
    InterviewDerivedCaseSummary,
    InterviewDetailResponse,
    InterviewProgress,
    InterviewQuestion,
    InterviewQuestionOption,
    InterviewQuestionType,
    InterviewRecordedAnswer,
    InterviewSessionStatus,
)
from backend.domain.cases.models import TranspositionCase
from backend.domain.interviews.models import InterviewSession
from backend.services.shared.note_ranges import normalize_note_bounds, parse_note_name_to_midi


QUESTION_ORDER = [
    "instrument_identity",
    "challenge_areas",
    "comfort_range",
    "additional_context",
]

LOW_CONFIDENCE_PHRASES = (
    "not sure",
    "unsure",
    "maybe",
    "don't know",
    "do not know",
)

RANGE_PLACEHOLDER_VALUES = {
    "no",
    "no data",
    "n/a",
    "na",
    "unknown",
    "-",
}


def _is_effective_range_value(value: Optional[str]) -> bool:
    if value is None:
        return False

    normalized = value.strip().lower()
    if not normalized or normalized in RANGE_PLACEHOLDER_VALUES:
        return False

    return True


def _has_confirmed_constraints_for_upload(case: TranspositionCase) -> bool:
    return bool(
        case.instrument_identity
        and case.instrument_identity != "placeholder"
        and _is_effective_range_value(case.comfort_range_min)
        and _is_effective_range_value(case.comfort_range_max)
    )


def _question_definitions() -> dict[str, InterviewQuestion]:
    return {
        "instrument_identity": InterviewQuestion(
            id="instrument_identity",
            prompt="Which instrument should this transposition case target?",
            type=InterviewQuestionType.SINGLE_SELECT,
            helpText="Pick the main instrument context so the later range checks stay grounded.",
            options=[
                InterviewQuestionOption(value="trumpet-bb", label="B-flat Trumpet"),
                InterviewQuestionOption(value="alto-sax-eb", label="E-flat Alto Saxophone"),
                InterviewQuestionOption(value="clarinet-bb", label="B-flat Clarinet"),
                InterviewQuestionOption(value="flute", label="Flute"),
                InterviewQuestionOption(value="horn-f", label="F Horn"),
            ],
        ),
        "challenge_areas": InterviewQuestion(
            id="challenge_areas",
            prompt="Which areas usually feel risky or tiring for this player?",
            type=InterviewQuestionType.MULTI_SELECT,
            required=False,
            helpText="Choose all that apply. Leave it empty if nothing stands out.",
            options=[
                InterviewQuestionOption(value="high_register", label="High register"),
                InterviewQuestionOption(value="low_register", label="Low register"),
                InterviewQuestionOption(value="fast_articulation", label="Fast articulation"),
                InterviewQuestionOption(value="difficult_keys", label="Difficult keys"),
            ],
        ),
        "comfort_range": InterviewQuestion(
            id="comfort_range",
            prompt="What note range feels comfortable for this player right now?",
            type=InterviewQuestionType.NOTE_RANGE,
            helpText="Use note names like G3 and D5.",
        ),
        "additional_context": InterviewQuestion(
            id="additional_context",
            prompt="Any extra context about the player or the arrangement?",
            type=InterviewQuestionType.NOTE_TEXT,
            required=False,
            placeholder="Optional notes for the transposition case",
            helpText="This stays structured as a note field, not a free-form interview replacement.",
        ),
        "additional_context_follow_up": InterviewQuestion(
            id="additional_context_follow_up",
            prompt="Your note sounded uncertain. What should the system avoid assuming?",
            type=InterviewQuestionType.NOTE_TEXT,
            required=True,
            helpText="Clarify the uncertain part so the case keeps confirmed and inferred constraints separate.",
            placeholder="Example: avoid assuming an extended upper register.",
        ),
    }


def _progress_for(question_id: Optional[str], status_value: InterviewSessionStatus) -> InterviewProgress:
    if status_value == InterviewSessionStatus.COMPLETED:
        return InterviewProgress(currentStep=len(QUESTION_ORDER), totalSteps=len(QUESTION_ORDER), percentComplete=100)

    if question_id == "additional_context_follow_up":
        return InterviewProgress(currentStep=4, totalSteps=4, percentComplete=75)

    if question_id is None:
        return InterviewProgress(currentStep=1, totalSteps=4, percentComplete=0)

    step_index = QUESTION_ORDER.index(question_id) + 1
    percent_complete = int(((step_index - 1) / len(QUESTION_ORDER)) * 100)
    return InterviewProgress(currentStep=step_index, totalSteps=4, percentComplete=percent_complete)


def _recorded_answers(session_model: InterviewSession) -> list[InterviewRecordedAnswer]:
    answers = session_model.answers or []
    return [InterviewRecordedAnswer.model_validate(answer) for answer in answers]


def _build_summary(case: TranspositionCase, recorded_answers: list[InterviewRecordedAnswer]) -> InterviewDerivedCaseSummary:
    instrument_identity = case.instrument_identity
    difficult_keys: list[str] = []
    restricted_registers: list[str] = []
    comfort_range_min: Optional[str] = None
    comfort_range_max: Optional[str] = None
    notes: list[str] = []

    for answer in recorded_answers:
        if answer.questionId == "instrument_identity" and answer.value.selectedOption:
            instrument_identity = answer.value.selectedOption
        elif answer.questionId == "challenge_areas":
            if "difficult_keys" in answer.value.selectedOptions:
                difficult_keys.append("needs_clarification")
            for selected in answer.value.selectedOptions:
                if selected in ("high_register", "low_register"):
                    restricted_registers.append(selected)
        elif answer.questionId == "comfort_range" and answer.value.noteRange is not None:
            comfort_range_min = answer.value.noteRange.min
            comfort_range_max = answer.value.noteRange.max
        elif answer.questionType == InterviewQuestionType.NOTE_TEXT and answer.value.text:
            notes.append(answer.value.text)

    confirmed_constraint_count = 0
    if instrument_identity:
        confirmed_constraint_count += 1
    if restricted_registers or difficult_keys:
        confirmed_constraint_count += 1
    if comfort_range_min and comfort_range_max:
        confirmed_constraint_count += 1

    return InterviewDerivedCaseSummary(
        caseStatus=case.status,
        instrumentIdentity=instrument_identity,
        difficultKeys=difficult_keys,
        restrictedRegisters=restricted_registers,
        comfortRangeMin=comfort_range_min,
        comfortRangeMax=comfort_range_max,
        notes=notes,
        confirmedConstraintCount=confirmed_constraint_count,
    )


def _validate_answer(question: InterviewQuestion, answer: InterviewAnswerValue) -> None:
    if question.type == InterviewQuestionType.SINGLE_SELECT:
        allowed_values = {option.value for option in question.options}
        if answer.selectedOption is None or answer.selectedOption not in allowed_values:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="selectedOption must match one of the approved options.",
            )
        return

    if question.type == InterviewQuestionType.MULTI_SELECT:
        allowed_values = {option.value for option in question.options}
        invalid_values = [value for value in answer.selectedOptions if value not in allowed_values]
        if invalid_values:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="selectedOptions contains unsupported values.",
            )
        return

    if question.type == InterviewQuestionType.NOTE_RANGE:
        if answer.noteRange is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="noteRange is required for note_range questions.",
            )
        note_min = answer.noteRange.min.strip()
        note_max = answer.noteRange.max.strip()
        if _is_effective_range_value(note_min) != _is_effective_range_value(note_max):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="noteRange must provide either two supported note names or two placeholder values.",
            )
        if _is_effective_range_value(note_min):
            try:
                parse_note_name_to_midi(note_min)
                parse_note_name_to_midi(note_max)
            except ValueError as error:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="noteRange must use supported note names like G3 to D5.",
                ) from error
        return

    if question.type == InterviewQuestionType.NOTE_TEXT:
        if question.required and (answer.text is None or not answer.text.strip()):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="text is required for note_text questions.",
            )


def _build_record(question: InterviewQuestion, answer: InterviewAnswerValue, low_confidence_flag: bool = False) -> dict:
    return {
        "questionId": question.id,
        "questionType": question.type,
        "value": answer.model_dump(),
        "lowConfidenceFlag": low_confidence_flag,
        "answeredAt": datetime.now(timezone.utc).isoformat(),
    }


def _apply_answer_to_case(case: TranspositionCase, question: InterviewQuestion, answer: InterviewAnswerValue) -> None:
    if question.id == "instrument_identity" and answer.selectedOption:
        case.instrument_identity = answer.selectedOption
        return

    if question.id == "challenge_areas":
        selected_options = answer.selectedOptions or []
        case.restricted_registers = [
            value for value in selected_options if value in ("high_register", "low_register")
        ]
        case.difficult_keys = ["needs_clarification"] if "difficult_keys" in selected_options else []
        return

    if question.id == "comfort_range" and answer.noteRange is not None:
        case.comfort_range_min = answer.noteRange.min
        case.comfort_range_max = answer.noteRange.max
        return


def _normalize_interview_answer(question: InterviewQuestion, answer: InterviewAnswerValue) -> None:
    if question.type != InterviewQuestionType.NOTE_RANGE or answer.noteRange is None:
        return

    note_min = answer.noteRange.min.strip()
    note_max = answer.noteRange.max.strip()
    if not _is_effective_range_value(note_min):
        answer.noteRange.min = note_min
        answer.noteRange.max = note_max
        return

    normalized_min, normalized_max = normalize_note_bounds(note_min, note_max)
    answer.noteRange.min = normalized_min
    answer.noteRange.max = normalized_max


def _sync_case_status(case: TranspositionCase, session_model: InterviewSession) -> None:
    if session_model.status == InterviewSessionStatus.COMPLETED and _has_confirmed_constraints_for_upload(case):
        case.status = CaseStatus.READY_FOR_UPLOAD
        return

    case.status = CaseStatus.INTERVIEW_IN_PROGRESS


def _next_question_id(current_question_id: str) -> Optional[str]:
    if current_question_id not in QUESTION_ORDER:
        return None
    current_index = QUESTION_ORDER.index(current_question_id)
    if current_index + 1 >= len(QUESTION_ORDER):
        return None
    return QUESTION_ORDER[current_index + 1]


class InterviewService:
    @staticmethod
    def start_or_continue(db: Session, payload: InterviewAdvanceRequest) -> InterviewAdvanceResponse:
        case = db.query(TranspositionCase).filter(TranspositionCase.id == payload.caseId).first()
        if case is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Case with id {payload.caseId} not found.",
            )

        definitions = _question_definitions()

        if payload.interviewId is None:
            if payload.restart:
                db.query(InterviewSession).filter(InterviewSession.case_id == payload.caseId).delete(
                    synchronize_session=False
                )
                case.status = CaseStatus.INTERVIEW_IN_PROGRESS
                db.add(case)
                db.commit()
                db.refresh(case)

                session_model = InterviewSession(
                    case_id=payload.caseId,
                    status=InterviewSessionStatus.IN_PROGRESS,
                    current_question_id=QUESTION_ORDER[0],
                    answers=[],
                    low_confidence={"active": False},
                )
                db.add(session_model)
                db.commit()
                db.refresh(session_model)

                return InterviewAdvanceResponse(
                    interviewId=session_model.id,
                    caseId=payload.caseId,
                    status=session_model.status,
                    nextQuestion=definitions[QUESTION_ORDER[0]],
                    progress=_progress_for(session_model.current_question_id, session_model.status),
                    lowConfidence=False,
                    collectedAnswers=[],
                    derivedCaseSummary=_build_summary(case, []),
                )

            existing_session = (
                db.query(InterviewSession)
                .filter(InterviewSession.case_id == payload.caseId)
                .order_by(InterviewSession.updated_at.desc())
                .first()
            )
            if existing_session is not None and existing_session.status != InterviewSessionStatus.COMPLETED:
                _sync_case_status(case, existing_session)
                db.add(case)
                db.commit()
                db.refresh(case)
                recorded_answers = _recorded_answers(existing_session)
                current_question = definitions.get(existing_session.current_question_id or QUESTION_ORDER[0])
                return InterviewAdvanceResponse(
                    interviewId=existing_session.id,
                    caseId=payload.caseId,
                    status=existing_session.status,
                    nextQuestion=current_question,
                    progress=_progress_for(existing_session.current_question_id, existing_session.status),
                    lowConfidence=bool((existing_session.low_confidence or {}).get("active")),
                    collectedAnswers=recorded_answers,
                    derivedCaseSummary=_build_summary(case, recorded_answers),
                )

            if existing_session is not None and existing_session.status == InterviewSessionStatus.COMPLETED:
                _sync_case_status(case, existing_session)
                db.add(case)
                db.commit()
                db.refresh(case)
                recorded_answers = _recorded_answers(existing_session)
                return InterviewAdvanceResponse(
                    interviewId=existing_session.id,
                    caseId=payload.caseId,
                    status=existing_session.status,
                    nextQuestion=None,
                    progress=_progress_for(None, existing_session.status),
                    lowConfidence=False,
                    collectedAnswers=recorded_answers,
                    derivedCaseSummary=_build_summary(case, recorded_answers),
                )

            session_model = InterviewSession(
                case_id=payload.caseId,
                status=InterviewSessionStatus.IN_PROGRESS,
                current_question_id=QUESTION_ORDER[0],
                answers=[],
                low_confidence={"active": False},
            )
            case.status = CaseStatus.INTERVIEW_IN_PROGRESS
            db.add(session_model)
            db.add(case)
            db.commit()
            db.refresh(session_model)
            db.refresh(case)

            return InterviewAdvanceResponse(
                interviewId=session_model.id,
                caseId=payload.caseId,
                status=session_model.status,
                nextQuestion=definitions[QUESTION_ORDER[0]],
                progress=_progress_for(QUESTION_ORDER[0], session_model.status),
                lowConfidence=False,
                collectedAnswers=[],
                derivedCaseSummary=_build_summary(case, []),
            )

        session_model = db.query(InterviewSession).filter(InterviewSession.id == payload.interviewId).first()
        if session_model is None or session_model.case_id != payload.caseId:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Interview with id {payload.interviewId} not found.",
            )

        if session_model.status == InterviewSessionStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="The interview session is already completed.",
            )

        expected_question_id = session_model.current_question_id or QUESTION_ORDER[0]
        if payload.questionId != expected_question_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="questionId does not match the current interview state.",
            )

        current_question = definitions[expected_question_id]
        assert payload.answer is not None
        _validate_answer(current_question, payload.answer)
        _normalize_interview_answer(current_question, payload.answer)

        answers = list(session_model.answers or [])
        low_confidence_flag = False

        if current_question.id == "additional_context" and payload.answer.text:
            normalized_text = payload.answer.text.lower()
            low_confidence_flag = any(marker in normalized_text for marker in LOW_CONFIDENCE_PHRASES)

        answers.append(_build_record(current_question, payload.answer, low_confidence_flag=low_confidence_flag))
        session_model.answers = answers
        _apply_answer_to_case(case, current_question, payload.answer)

        if low_confidence_flag:
            session_model.status = InterviewSessionStatus.AWAITING_FOLLOW_UP
            session_model.current_question_id = "additional_context_follow_up"
            session_model.low_confidence = {"active": True, "reason": "uncertain_additional_context"}
        elif current_question.id == "additional_context_follow_up":
            session_model.status = InterviewSessionStatus.COMPLETED
            session_model.current_question_id = None
            session_model.low_confidence = {"active": False}
        else:
            next_question_id = _next_question_id(current_question.id)
            if next_question_id is None:
                session_model.status = InterviewSessionStatus.COMPLETED
                session_model.current_question_id = None
                session_model.low_confidence = {"active": False}
            else:
                session_model.status = InterviewSessionStatus.IN_PROGRESS
                session_model.current_question_id = next_question_id
                session_model.low_confidence = {"active": False}

        _sync_case_status(case, session_model)
        db.add(session_model)
        db.add(case)
        db.commit()
        db.refresh(session_model)
        db.refresh(case)

        next_question = definitions.get(session_model.current_question_id) if session_model.current_question_id else None
        derived_summary = _build_summary(case, _recorded_answers(session_model))

        return InterviewAdvanceResponse(
            interviewId=session_model.id,
            caseId=payload.caseId,
            status=session_model.status,
            nextQuestion=next_question,
            progress=_progress_for(session_model.current_question_id, session_model.status),
            lowConfidence=bool((session_model.low_confidence or {}).get("active")),
            collectedAnswers=_recorded_answers(session_model),
            derivedCaseSummary=derived_summary,
        )

    @staticmethod
    def get_detail(db: Session, interview_id: str) -> InterviewDetailResponse:
        session_model = db.query(InterviewSession).filter(InterviewSession.id == interview_id).first()
        if session_model is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Interview with id {interview_id} not found.",
            )

        case = db.query(TranspositionCase).filter(TranspositionCase.id == session_model.case_id).first()
        if case is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Case with id {session_model.case_id} not found.",
            )

        definitions = _question_definitions()
        recorded_answers = _recorded_answers(session_model)

        return InterviewDetailResponse(
            interviewId=session_model.id,
            caseId=session_model.case_id,
            status=session_model.status,
            currentQuestion=definitions.get(session_model.current_question_id) if session_model.current_question_id else None,
            progress=_progress_for(session_model.current_question_id, session_model.status),
            lowConfidence=bool((session_model.low_confidence or {}).get("active")),
            collectedAnswers=recorded_answers,
            derivedCaseSummary=_build_summary(case, recorded_answers),
        )
