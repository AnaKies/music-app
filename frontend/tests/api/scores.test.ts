import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

import { scoresApi } from '../../shared/api/scores';

const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('Scores API Client', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    process.env.NEXT_PUBLIC_API_URL = 'http://localhost:8000';
  });

  afterEach(() => {
    delete process.env.NEXT_PUBLIC_API_URL;
  });

  it('uploads a score through the multipart endpoint', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        scoreDocumentId: 'score-123',
        format: 'musicxml',
        acceptedStatus: 'uploaded',
        originalFilename: 'example.musicxml',
        initialProcessingSnapshot: {
          scoreDocumentId: 'score-123',
          transpositionCaseId: 'case-123',
          processingStatus: 'uploaded',
          acceptedAt: '2026-03-19T10:00:00Z',
        },
      }),
    });

    const file = new File(['<score-partwise></score-partwise>'], 'example.musicxml', {
      type: 'application/xml',
    });

    const result = await scoresApi.uploadScore('case-123', file);

    expect(mockFetch).toHaveBeenCalledWith(
      'http://localhost:8000/scores',
      expect.objectContaining({
        method: 'POST',
        body: expect.any(FormData),
      })
    );
    expect(result.acceptedStatus).toBe('uploaded');
  });
});
