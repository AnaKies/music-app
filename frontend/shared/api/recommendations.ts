import { ApiError } from './cases';
import type { RecommendationResponse } from '@/shared/types/recommendations';

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

export const recommendationsApi = {
  async generateRecommendations(
    transpositionCaseId: string,
    scoreDocumentId: string
  ): Promise<RecommendationResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/recommendations`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          transpositionCaseId,
          scoreDocumentId,
        }),
      });

      return handleResponse<RecommendationResponse>(response);
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
