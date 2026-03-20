/**
 * TypeScript types for transposition cases.
 * 
 * These types mirror the Pydantic schemas from backend/api/schemas/cases.py
 * to ensure type safety across the frontend-backend boundary.
 */

/**
 * Case status values matching backend CaseStatus enum.
 * @see backend/api/schemas/cases.py::CaseStatus
 */
export type CaseStatus =
  | 'new'
  | 'interview_in_progress'
  | 'ready_for_upload'
  | 'recommendation_ready'
  | 'completed'
  | 'archived';

/**
 * User-specific playable constraints for a transposition case.
 * Matches backend CaseConstraints schema.
 * @see backend/api/schemas/cases.py::CaseConstraints
 */
export interface CaseConstraints {
  highest_playable_tone: string | null;
  lowest_playable_tone: string | null;
  restricted_tones: string[];
  restricted_registers: string[];
  difficult_keys: string[];
  preferred_keys: string[];
  comfort_range_min: string | null;
  comfort_range_max: string | null;
}

/**
 * Case summary for list and overview displays.
 * Matches backend CaseSummary schema.
 * @see backend/api/schemas/cases.py::CaseSummary
 */
export interface CaseSummary {
  id: string;
  status: CaseStatus;
  instrumentIdentity: string;
  scoreCount: number;
  createdAt: string; // ISO 8601 datetime
  updatedAt: string; // ISO 8601 datetime
}

/**
 * Detailed case information including constraints.
 * Matches backend CaseDetail schema.
 * @see backend/api/schemas/cases.py::CaseDetail
 */
export interface CaseDetail extends CaseSummary {
  latestScoreDocumentId?: string | null;
  constraints: CaseConstraints;
}

/**
 * Response from POST /cases endpoint.
 * Matches backend CaseCreateResponse schema.
 * @see backend/api/schemas/cases.py::CaseCreateResponse
 */
export interface CaseCreateResponse {
  transpositionCaseId: string;
  status: CaseStatus;
  caseSummary: CaseSummary;
}

/**
 * Request payload for creating a new case.
 * Matches backend CaseCreateRequest schema.
 * @see backend/api/schemas/cases.py::CaseCreateRequest
 */
export interface CaseCreateRequest {
  instrument_identity: string;
  existing_case_action?: 'reset' | null;
  existing_case_id?: string | null;
}

/**
 * Action type for case creation flow.
 */
export type CaseAction = 'create' | 'reset' | 'continue';
