export type RecommendationConfidence = 'high' | 'medium' | 'low' | 'blocked';
export type RecommendationStatus = 'ready' | 'blocked';
export type RecommendationWarningSeverity = 'info' | 'warning' | 'blocker';

export interface RecommendationWarning {
  code: string;
  severity: RecommendationWarningSeverity;
  message: string;
}

export interface RecommendationTargetRange {
  min: string;
  max: string;
}

export interface RecommendationItem {
  recommendationId: string;
  label: string;
  targetRange: RecommendationTargetRange;
  recommendedKey?: string | null;
  confidence: RecommendationConfidence;
  summaryReason: string;
  warnings: RecommendationWarning[];
  isPrimary: boolean;
}

export interface RecommendationFailure {
  confidence: RecommendationConfidence;
  code: string;
  safeSummary: string;
}

export interface RecommendationResponse {
  status: RecommendationStatus;
  transpositionCaseId: string;
  scoreDocumentId: string;
  recommendations: RecommendationItem[];
  failure?: RecommendationFailure | null;
}
