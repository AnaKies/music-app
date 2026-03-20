from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, model_validator

from backend.api.schemas.cases import CaseStatus


class InterviewQuestionType(str, Enum):
    SINGLE_SELECT = "single_select"
    MULTI_SELECT = "multi_select"
    NOTE_RANGE = "note_range"
    NOTE_TEXT = "note_text"


class InterviewSessionStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    AWAITING_FOLLOW_UP = "awaiting_follow_up"
    COMPLETED = "completed"


class InterviewQuestionOption(BaseModel):
    value: str
    label: str
    description: Optional[str] = None


class InterviewQuestion(BaseModel):
    id: str
    prompt: str
    type: InterviewQuestionType
    required: bool = True
    helpText: Optional[str] = None
    placeholder: Optional[str] = None
    options: list[InterviewQuestionOption] = Field(default_factory=list)


class InterviewNoteRangeAnswer(BaseModel):
    min: str = Field(min_length=1)
    max: str = Field(min_length=1)


class InterviewAnswerValue(BaseModel):
    selectedOption: Optional[str] = None
    selectedOptions: list[str] = Field(default_factory=list)
    noteRange: Optional[InterviewNoteRangeAnswer] = None
    text: Optional[str] = None


class InterviewAdvanceRequest(BaseModel):
    caseId: str = Field(min_length=1)
    interviewId: Optional[str] = None
    questionId: Optional[str] = None
    answer: Optional[InterviewAnswerValue] = None
    restart: bool = False

    @model_validator(mode="after")
    def validate_start_or_continue(self):
        if self.interviewId is None and self.questionId is None and self.answer is None:
            return self

        if self.interviewId is None:
            raise ValueError("interviewId is required when advancing an interview.")
        if self.questionId is None:
            raise ValueError("questionId is required when advancing an interview.")
        if self.answer is None:
            raise ValueError("answer is required when advancing an interview.")

        return self


class InterviewRecordedAnswer(BaseModel):
    questionId: str
    questionType: InterviewQuestionType
    value: InterviewAnswerValue
    lowConfidenceFlag: bool = False
    answeredAt: datetime


class InterviewProgress(BaseModel):
    currentStep: int
    totalSteps: int
    percentComplete: int


class InterviewDerivedCaseSummary(BaseModel):
    caseStatus: CaseStatus
    instrumentIdentity: Optional[str] = None
    difficultKeys: list[str] = Field(default_factory=list)
    restrictedRegisters: list[str] = Field(default_factory=list)
    comfortRangeMin: Optional[str] = None
    comfortRangeMax: Optional[str] = None
    notes: list[str] = Field(default_factory=list)
    confirmedConstraintCount: int = 0


class InterviewAdvanceResponse(BaseModel):
    interviewId: str
    caseId: str
    status: InterviewSessionStatus
    nextQuestion: Optional[InterviewQuestion] = None
    progress: InterviewProgress
    lowConfidence: bool = False
    collectedAnswers: list[InterviewRecordedAnswer] = Field(default_factory=list)
    derivedCaseSummary: InterviewDerivedCaseSummary


class InterviewDetailResponse(BaseModel):
    interviewId: str
    caseId: str
    status: InterviewSessionStatus
    currentQuestion: Optional[InterviewQuestion] = None
    progress: InterviewProgress
    lowConfidence: bool = False
    collectedAnswers: list[InterviewRecordedAnswer] = Field(default_factory=list)
    derivedCaseSummary: InterviewDerivedCaseSummary


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
