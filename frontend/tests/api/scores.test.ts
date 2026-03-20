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
        acceptedStatus: 'parsed',
        originalFilename: 'example.musicxml',
        initialProcessingSnapshot: {
          scoreDocumentId: 'score-123',
          transpositionCaseId: 'case-123',
          processingStatus: 'parsed',
          acceptedAt: '2026-03-19T10:00:00Z',
          canonicalScoreSummary: {
            schemaVersion: 'v1',
            title: null,
            partCount: 1,
            measureCount: 1,
            noteCount: 1,
            restCount: 0,
            parts: [{ partId: 'P1', name: 'Flute' }],
          },
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
    expect(result.acceptedStatus).toBe('parsed');
  });

  it('loads the source-score preview contract', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        scoreDocumentId: 'score-123',
        artifactRole: 'source',
        availability: 'ready',
        rendererFormat: 'musicxml_preview',
        pageCount: 1,
        revisionToken: '2026-03-20T10:00:00+00:00',
        safeSummary: 'The uploaded score is ready for read-only preview.',
        previewAccess: 'preview:score-123:2026-03-20T10:00:00+00:00',
        originalFilename: 'example.musicxml',
        canonicalScoreSummary: {
          schemaVersion: 'v1',
          title: null,
          partCount: 1,
          measureCount: 1,
          noteCount: 1,
          restCount: 0,
          parts: [{ partId: 'P1', name: 'Flute' }],
        },
      }),
    });

    const result = await scoresApi.getScorePreview('score-123');

    expect(mockFetch).toHaveBeenCalledWith('http://localhost:8000/scores/score-123/preview');
    expect(result.availability).toBe('ready');
    expect(result.artifactRole).toBe('source');
  });
});
