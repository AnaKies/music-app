export type InterviewQuestionType =
  | 'single_select'
  | 'multi_select'
  | 'note_range'
  | 'note_text';

export type InterviewSessionStatus =
  | 'in_progress'
  | 'awaiting_follow_up'
  | 'completed';

export interface InterviewQuestionOption {
  value: string;
  label: string;
  description?: string | null;
}

export interface InterviewQuestion {
  id: string;
  prompt: string;
  type: InterviewQuestionType;
  required: boolean;
  helpText?: string | null;
  placeholder?: string | null;
  options: InterviewQuestionOption[];
}

export interface InterviewNoteRangeAnswer {
  min: string;
  max: string;
}

export interface InterviewAnswerValue {
  selectedOption?: string | null;
  selectedOptions?: string[];
  noteRange?: InterviewNoteRangeAnswer | null;
  text?: string | null;
}

export interface InterviewAdvanceRequest {
  caseId: string;
  interviewId?: string;
  questionId?: string;
  answer?: InterviewAnswerValue;
  restart?: boolean;
}

export interface InterviewRecordedAnswer {
  questionId: string;
  questionType: InterviewQuestionType;
  value: InterviewAnswerValue;
  lowConfidenceFlag: boolean;
  answeredAt: string;
}

export interface InterviewProgress {
  currentStep: number;
  totalSteps: number;
  percentComplete: number;
}

export interface InterviewDerivedCaseSummary {
  caseStatus: string;
  instrumentIdentity?: string | null;
  difficultKeys: string[];
  restrictedRegisters: string[];
  comfortRangeMin?: string | null;
  comfortRangeMax?: string | null;
  notes: string[];
  confirmedConstraintCount: number;
}

export interface InterviewAdvanceResponse {
  interviewId: string;
  caseId: string;
  status: InterviewSessionStatus;
  nextQuestion?: InterviewQuestion | null;
  progress: InterviewProgress;
  lowConfidence: boolean;
  derivedCaseSummary: InterviewDerivedCaseSummary;
}

export interface InterviewDetailResponse {
  interviewId: string;
  caseId: string;
  status: InterviewSessionStatus;
  currentQuestion?: InterviewQuestion | null;
  progress: InterviewProgress;
  lowConfidence: boolean;
  collectedAnswers: InterviewRecordedAnswer[];
  derivedCaseSummary: InterviewDerivedCaseSummary;
}
