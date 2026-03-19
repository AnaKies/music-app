import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { recommendationsApi } from '../../shared/api/recommendations';

const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('Recommendations API Client', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    process.env.NEXT_PUBLIC_API_URL = 'http://localhost:8000';
  });

  afterEach(() => {
    delete process.env.NEXT_PUBLIC_API_URL;
  });

  it('requests generated recommendations for a parsed score', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        status: 'ready',
        transpositionCaseId: 'case-123',
        scoreDocumentId: 'score-123',
        recommendations: [
          {
            recommendationId: 'rec-1',
            label: 'Primary recommendation',
            targetRange: { min: 'G3', max: 'D5' },
            recommendedKey: 'concert_c',
            confidence: 'medium',
            summaryReason: 'Matches the confirmed player comfort range.',
            warnings: [],
            isPrimary: true,
          },
        ],
        failure: null,
      }),
    });

    const result = await recommendationsApi.generateRecommendations('case-123', 'score-123');

    expect(mockFetch).toHaveBeenCalledWith(
      'http://localhost:8000/recommendations',
      expect.objectContaining({
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          transpositionCaseId: 'case-123',
          scoreDocumentId: 'score-123',
        }),
      })
    );
    expect(result.status).toBe('ready');
    expect(result.recommendations).toHaveLength(1);
  });
});
