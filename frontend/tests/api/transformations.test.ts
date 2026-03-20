import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { transformationsApi } from '../../shared/api/transformations';

const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('Transformations API Client', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    process.env.NEXT_PUBLIC_API_URL = 'http://localhost:8000';
  });

  afterEach(() => {
    delete process.env.NEXT_PUBLIC_API_URL;
  });

  it('starts a deterministic transformation from a selected recommendation', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        transformationJobId: 'job-123',
        status: 'completed',
        transpositionCaseId: 'case-123',
        scoreDocumentId: 'score-123',
        recommendationId: 'rec-123',
        selectedRangeMin: 'G3',
        selectedRangeMax: 'D5',
        semitoneShift: -2,
        safeSummary: 'The deterministic transformation completed successfully.',
        warnings: [],
        createdAt: '2026-03-20T10:00:00Z',
      }),
    });

    const result = await transformationsApi.runTransformation('case-123', 'score-123', 'rec-123');

    expect(mockFetch).toHaveBeenCalledWith(
      'http://localhost:8000/transformations',
      expect.objectContaining({
        method: 'POST',
      })
    );
    expect(result.status).toBe('completed');
    expect(result.recommendationId).toBe('rec-123');
  });
});
