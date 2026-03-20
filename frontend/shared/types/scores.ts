export type ScoreFormat = 'musicxml';
export type ScoreProcessingStatus =
  | 'uploaded'
  | 'queued'
  | 'parsing'
  | 'parsed'
  | 'recommendation_pending'
  | 'recommendation_ready'
  | 'transforming'
  | 'completed'
  | 'failed'
  | 'parse_failed';
export type ParseFailureType = 'invalid_xml' | 'unsupported_structure' | 'empty_score';
export type ScorePreviewAvailability = 'ready' | 'not_ready' | 'unavailable' | 'failed';
export type ScoreArtifactRole = 'source' | 'result';

export interface CanonicalScorePartSummary {
  partId: string;
  name: string;
}

export interface CanonicalScoreSummary {
  schemaVersion: string;
  title: string | null;
  partCount: number;
  measureCount: number;
  noteCount: number;
  restCount: number;
  parts: CanonicalScorePartSummary[];
}

export interface ScoreProcessingSnapshot {
  scoreDocumentId: string;
  transpositionCaseId: string;
  processingStatus: ScoreProcessingStatus;
  acceptedAt: string;
  parseFailureType?: ParseFailureType | null;
  canonicalScoreSummary?: CanonicalScoreSummary | null;
}

export interface ScoreUploadResponse {
  scoreDocumentId: string;
  format: ScoreFormat;
  acceptedStatus: ScoreProcessingStatus;
  initialProcessingSnapshot: ScoreProcessingSnapshot;
  originalFilename: string;
}

export interface ScorePreviewResponse {
  scoreDocumentId: string;
  artifactRole: ScoreArtifactRole;
  availability: ScorePreviewAvailability;
  rendererFormat?: string | null;
  pageCount?: number | null;
  revisionToken?: string | null;
  safeSummary: string;
  failureCode?: string | null;
  failureSeverity?: string | null;
  previewAccess?: string | null;
  originalFilename?: string | null;
  canonicalScoreSummary?: CanonicalScoreSummary | null;
}

export interface ScoreReadResponse {
  scoreDocumentId: string;
  transpositionCaseId: string;
  processingStatus: ScoreProcessingStatus;
  originalFilename: string;
  safeSummary: string;
  latestTransformationJobId?: string | null;
  sourcePreview?: ScorePreviewResponse | null;
  resultPreview?: ScorePreviewResponse | null;
}
