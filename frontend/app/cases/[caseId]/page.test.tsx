import { render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent } from '@testing-library/react';

import CaseDetailPage from './page';
import { casesApi } from '@/shared/api/cases';
import { scoresApi } from '@/shared/api/scores';

vi.mock('@/shared/api/cases', () => ({
  casesApi: {
    getCase: vi.fn(),
  },
  ApiError: class ApiError extends Error {
    constructor(message: string, public status: number) {
      super(message);
      this.name = 'ApiError';
    }
  },
}));

vi.mock('@/shared/api/scores', () => ({
  scoresApi: {
    uploadScore: vi.fn(),
  },
}));

vi.mock('next/navigation', () => ({
  useParams: () => ({
    caseId: 'existing-case-1',
  }),
}));

describe('CaseDetailPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('loads the selected case and renders the case overview', async () => {
    vi.mocked(casesApi.getCase).mockResolvedValue({
      id: 'existing-case-1',
      status: 'ready_for_upload',
      instrumentIdentity: 'trumpet-bb',
      scoreCount: 2,
      createdAt: '2024-01-15T10:00:00Z',
      updatedAt: '2024-01-16T12:00:00Z',
      constraints: {
        highest_playable_tone: 'G5',
        lowest_playable_tone: 'E3',
        restricted_tones: [],
        restricted_registers: [],
        difficult_keys: [],
        preferred_keys: [],
        comfort_range_min: null,
        comfort_range_max: null,
      },
    });

    render(<CaseDetailPage />);

    await waitFor(() => {
      expect(casesApi.getCase).toHaveBeenCalledWith('existing-case-1');
    });

    expect(await screen.findByText('Case overview')).toBeInTheDocument();
    expect(screen.getByText('trumpet-bb')).toBeInTheDocument();
    expect(screen.getByText('Status: ready_for_upload')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /upload musicxml/i })).toBeDisabled();
  });

  it('offers an interview action for in-progress cases', async () => {
    vi.mocked(casesApi.getCase).mockResolvedValue({
      id: 'existing-case-1',
      status: 'interview_in_progress',
      instrumentIdentity: 'trumpet-bb',
      scoreCount: 0,
      createdAt: '2024-01-15T10:00:00Z',
      updatedAt: '2024-01-16T12:00:00Z',
      constraints: {
        highest_playable_tone: null,
        lowest_playable_tone: null,
        restricted_tones: [],
        restricted_registers: [],
        difficult_keys: [],
        preferred_keys: [],
        comfort_range_min: null,
        comfort_range_max: null,
      },
    });

    render(<CaseDetailPage />);

    expect(await screen.findByRole('link', { name: /continue interview/i })).toHaveAttribute(
      'href',
      '/interview?caseId=existing-case-1'
    );
  });

  it('does not offer an interview action for completed cases', async () => {
    vi.mocked(casesApi.getCase).mockResolvedValue({
      id: 'existing-case-1',
      status: 'completed',
      instrumentIdentity: 'trumpet-bb',
      scoreCount: 1,
      createdAt: '2024-01-15T10:00:00Z',
      updatedAt: '2024-01-16T12:00:00Z',
      constraints: {
        highest_playable_tone: null,
        lowest_playable_tone: null,
        restricted_tones: [],
        restricted_registers: [],
        difficult_keys: [],
        preferred_keys: [],
        comfort_range_min: null,
        comfort_range_max: null,
      },
    });

    render(<CaseDetailPage />);

    await screen.findByText('Case overview');
    expect(screen.queryByRole('link', { name: /interview/i })).not.toBeInTheDocument();
  });

  it('uploads a MusicXML file for ready cases', async () => {
    vi.mocked(casesApi.getCase)
      .mockResolvedValueOnce({
        id: 'existing-case-1',
        status: 'ready_for_upload',
        instrumentIdentity: 'trumpet-bb',
        scoreCount: 0,
        createdAt: '2024-01-15T10:00:00Z',
        updatedAt: '2024-01-16T12:00:00Z',
        constraints: {
          highest_playable_tone: null,
          lowest_playable_tone: null,
          restricted_tones: [],
          restricted_registers: [],
          difficult_keys: [],
          preferred_keys: [],
          comfort_range_min: 'G3',
          comfort_range_max: 'D5',
        },
      })
      .mockResolvedValueOnce({
        id: 'existing-case-1',
        status: 'ready_for_upload',
        instrumentIdentity: 'trumpet-bb',
        scoreCount: 1,
        createdAt: '2024-01-15T10:00:00Z',
        updatedAt: '2024-01-16T12:00:00Z',
        constraints: {
          highest_playable_tone: null,
          lowest_playable_tone: null,
          restricted_tones: [],
          restricted_registers: [],
          difficult_keys: [],
          preferred_keys: [],
          comfort_range_min: 'G3',
          comfort_range_max: 'D5',
        },
      });
    vi.mocked(scoresApi.uploadScore).mockResolvedValue({
      scoreDocumentId: 'score-123',
      format: 'musicxml',
      acceptedStatus: 'parsed',
      originalFilename: 'example.musicxml',
      initialProcessingSnapshot: {
        scoreDocumentId: 'score-123',
        transpositionCaseId: 'existing-case-1',
        processingStatus: 'parsed',
        acceptedAt: '2026-03-19T10:00:00Z',
        canonicalScoreSummary: {
          schemaVersion: 'v1',
          title: null,
          partCount: 1,
          measureCount: 1,
          noteCount: 0,
          restCount: 1,
          parts: [{ partId: 'P1', name: 'Flute' }],
        },
      },
    });

    render(<CaseDetailPage />);

    const fileInput = await screen.findByLabelText('MusicXML file');
    const file = new File(['<score-partwise></score-partwise>'], 'example.musicxml', { type: 'application/xml' });
    fireEvent.change(fileInput, { target: { files: [file] } });
    fireEvent.click(screen.getByRole('button', { name: /upload musicxml/i }));

    await waitFor(() => {
      expect(scoresApi.uploadScore).toHaveBeenCalledWith('existing-case-1', file);
    });
    expect(await screen.findByText('Score parsed successfully')).toBeInTheDocument();
    expect(screen.getByText(/Parsed 1 part\(s\) across 1 measure\(s\)\./i)).toBeInTheDocument();
  });
});
