export type TransformationStatus = 'completed' | 'failed';
export type TransformationWarningSeverity = 'info' | 'warning' | 'blocker';

export interface TransformationWarning {
  code: string;
  severity: TransformationWarningSeverity;
  message: string;
}

export interface TransformationResponse {
  transformationJobId: string;
  status: TransformationStatus;
  transpositionCaseId: string;
  scoreDocumentId: string;
  recommendationId: string;
  selectedRangeMin: string;
  selectedRangeMax: string;
  semitoneShift?: number | null;
  safeSummary: string;
  resultFilename?: string | null;
  resultPreviewRevisionToken?: string | null;
  isRetryable: boolean;
  failureCode?: string | null;
  failureSeverity?: string | null;
  warnings: TransformationWarning[];
  createdAt: string;
}
