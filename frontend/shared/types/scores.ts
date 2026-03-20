export type ScoreFormat = 'musicxml';
export type ScoreProcessingStatus = 'uploaded' | 'parsed' | 'parse_failed';
export type ParseFailureType = 'invalid_xml' | 'unsupported_structure' | 'empty_score';

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
