from pydantic import ValidationError
import pytest

from backend.api.schemas.interviews import (
    InterviewAdvanceRequest,
    InterviewAnswerValue,
    InterviewQuestion,
    InterviewQuestionOption,
    InterviewQuestionType,
)


def test_interview_question_schema_supports_structured_rendering():
    question = InterviewQuestion(
        id="instrument_identity",
        prompt="Which instrument should this transposition case target?",
        type=InterviewQuestionType.SINGLE_SELECT,
        required=True,
        helpText="Pick the main instrument context.",
        options=[
            InterviewQuestionOption(value="trumpet-bb", label="B-flat Trumpet"),
        ],
    )

    data = question.model_dump()
    assert data["type"] == "single_select"
    assert data["options"][0]["value"] == "trumpet-bb"


def test_interview_answer_value_supports_multiple_structured_shapes():
    answer = InterviewAnswerValue(
        selectedOptions=["high_register", "difficult_keys"],
        noteRange={"min": "G3", "max": "D5"},
        text="not sure about the upper register",
    )

    dumped = answer.model_dump()
    assert dumped["selectedOptions"] == ["high_register", "difficult_keys"]
    assert dumped["noteRange"]["min"] == "G3"
    assert dumped["text"] == "not sure about the upper register"


def test_interview_advance_request_allows_start_and_continue_shapes():
    start_request = InterviewAdvanceRequest(caseId="case-1")
    assert start_request.interviewId is None

    continue_request = InterviewAdvanceRequest(
        caseId="case-1",
        interviewId="interview-1",
        questionId="instrument_identity",
        answer={"selectedOption": "trumpet-bb"},
    )
    assert continue_request.interviewId == "interview-1"
    assert continue_request.answer is not None


def test_interview_advance_request_rejects_partial_continue_payload():
    with pytest.raises(ValidationError):
        InterviewAdvanceRequest(
            caseId="case-1",
            interviewId="interview-1",
        )
