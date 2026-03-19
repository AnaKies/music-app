export type ScoreFormat = 'musicxml';
export type ScoreProcessingStatus = 'uploaded';

export interface ScoreProcessingSnapshot {
  scoreDocumentId: string;
  transpositionCaseId: string;
  processingStatus: ScoreProcessingStatus;
  acceptedAt: string;
}

export interface ScoreUploadResponse {
  scoreDocumentId: string;
  format: ScoreFormat;
  acceptedStatus: ScoreProcessingStatus;
  initialProcessingSnapshot: ScoreProcessingSnapshot;
  originalFilename: string;
}
