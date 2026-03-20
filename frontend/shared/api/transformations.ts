import { ApiError } from './cases';
import type { TransformationResponse } from '@/shared/types/transformations';

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

export const transformationsApi = {
  async runTransformation(
    transpositionCaseId: string,
    scoreDocumentId: string,
    recommendationId: string
  ): Promise<TransformationResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/transformations`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          transpositionCaseId,
          scoreDocumentId,
          recommendationId,
        }),
      });

      return handleResponse<TransformationResponse>(response);
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
