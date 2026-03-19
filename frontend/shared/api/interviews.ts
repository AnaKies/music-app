import { ApiError } from './cases';
import type {
  InterviewAdvanceRequest,
  InterviewAdvanceResponse,
  InterviewDetailResponse,
} from '@/shared/types/interviews';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new ApiError(
      errorData.detail || `Request failed with status ${response.status}`,
      response.status,
      errorData.code
    );
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

export const interviewsApi = {
  async startOrContinueInterview(
    request: InterviewAdvanceRequest
  ): Promise<InterviewAdvanceResponse> {
    return performRequest<InterviewAdvanceResponse>(`${API_BASE_URL}/interviews`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });
  },

  async getInterview(interviewId: string): Promise<InterviewDetailResponse> {
    return performRequest<InterviewDetailResponse>(`${API_BASE_URL}/interviews/${interviewId}`, {
      method: 'GET',
      headers: {
        Accept: 'application/json',
      },
    });
  },
};
