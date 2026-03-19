/**
 * API client for case-related endpoints.
 * 
 * Provides type-safe access to the backend case management API.
 * All methods handle errors and return typed responses.
 */

import type {
  CaseSummary,
  CaseDetail,
  CaseCreateRequest,
  CaseCreateResponse,
} from '../types/cases';

// API base URL from environment or default
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Custom error class for API-related errors.
 */
export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public code?: string
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

/**
 * Handle API response and throw typed errors.
 */
async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new ApiError(
      errorData.detail || `Request failed with status ${response.status}`,
      response.status,
      errorData.code
    );
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return response.json();
}

async function performRequest<T>(input: RequestInfo | URL, init?: RequestInit): Promise<T> {
  try {
    const response = await fetch(input, init);
    return handleResponse<T>(response);
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }

    throw new ApiError(
      'Could not reach the backend service. Please make sure the backend is running and try again.',
      0
    );
  }
}

/**
 * Case API client.
 */
export const casesApi = {
  /**
   * Create a new transposition case.
   * 
   * @param request - Case creation request with instrument identity
   * @returns Created case response with ID and summary
   * @throws ApiError on validation failure or server error
   */
  async createCase(request: CaseCreateRequest): Promise<CaseCreateResponse> {
    return performRequest<CaseCreateResponse>(`${API_BASE_URL}/cases`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });
  },

  /**
   * Retrieve a single case by ID.
   * 
   * @param caseId - Unique case identifier
   * @returns Full case details including constraints
   * @throws ApiError if case not found (404) or server error
   */
  async getCase(caseId: string): Promise<CaseDetail> {
    return performRequest<CaseDetail>(`${API_BASE_URL}/cases/${caseId}`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
      },
    });
  },

  /**
   * List all cases for the current user.
   * 
   * @returns Array of case summaries
   * @throws ApiError on server error
   */
  async listCases(): Promise<CaseSummary[]> {
    return performRequest<CaseSummary[]>(`${API_BASE_URL}/cases`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
      },
    });
  },

  /**
   * Delete a case through the provisional MVP cleanup route.
   *
   * @param caseId - Unique case identifier
   * @throws ApiError if the case cannot be deleted
   */
  async deleteCase(caseId: string): Promise<void> {
    await performRequest<void>(`${API_BASE_URL}/cases/${caseId}`, {
      method: 'DELETE',
      headers: {
        'Accept': 'application/json',
      },
    });
  },
};

export default casesApi;
