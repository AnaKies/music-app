import { ApiError } from './cases';
import type { ScoreUploadResponse } from '@/shared/types/scores';

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

export const scoresApi = {
  async uploadScore(transpositionCaseId: string, file: File): Promise<ScoreUploadResponse> {
    const formData = new FormData();
    formData.append('transpositionCaseId', transpositionCaseId);
    formData.append('file', file);

    try {
      const response = await fetch(`${API_BASE_URL}/scores`, {
        method: 'POST',
        body: formData,
      });

      return handleResponse<ScoreUploadResponse>(response);
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }

      throw new ApiError(
        'Could not reach the backend service. Please make sure the backend is running and try again.',
        0
      );
    }
  },
};
