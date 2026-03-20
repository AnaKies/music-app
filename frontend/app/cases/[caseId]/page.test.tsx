import { render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent } from '@testing-library/react';

import CaseDetailPage from './page';
import { casesApi } from '@/shared/api/cases';
import { recommendationsApi } from '@/shared/api/recommendations';
import { scoresApi } from '@/shared/api/scores';
import { transformationsApi } from '@/shared/api/transformations';

vi.mock('@/components/score-preview/ScoreViewer', () => ({
  ScoreViewer: ({ title }: { title: string }) => (
    <div>
      <div aria-label={`${title} score viewer`}>Mocked score viewer</div>
      <div aria-label="Score preview pagination">Mocked pagination</div>
    </div>
  ),
}));

vi.mock('@/shared/api/cases', () => ({
  casesApi: {
    getCase: vi.fn(),
    updateCase: vi.fn(),
    resetCase: vi.fn(),
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
    getScore: vi.fn(),
    getScorePreview: vi.fn(),
    getResultDownloadUrl: vi.fn((scoreDocumentId: string) => `http://localhost:8000/scores/${scoreDocumentId}/download?artifact=result`),
  },
}));

vi.mock('@/shared/api/recommendations', () => ({
  recommendationsApi: {
    getRecommendations: vi.fn(),
    generateRecommendations: vi.fn(),
  },
}));

vi.mock('@/shared/api/transformations', () => ({
  transformationsApi: {
    runTransformation: vi.fn(),
    getTransformation: vi.fn(),
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
    vi.stubGlobal('confirm', vi.fn(() => true));
    vi.mocked(recommendationsApi.getRecommendations).mockResolvedValue({
      status: 'ready',
      transpositionCaseId: 'existing-case-1',
      scoreDocumentId: 'score-123',
      recommendations: [],
      failure: null,
    });
    vi.mocked(scoresApi.getResultDownloadUrl).mockImplementation(
      (scoreDocumentId: string) => `http://localhost:8000/scores/${scoreDocumentId}/download?artifact=result`
    );
  });

  it('loads the selected case and renders the case overview', async () => {
    vi.mocked(casesApi.getCase).mockResolvedValue({
      id: 'existing-case-1',
      status: 'ready_for_upload',
      instrumentIdentity: 'trumpet-bb',
      scoreCount: 2,
      createdAt: '2024-01-15T10:00:00Z',
      updatedAt: '2024-01-16T12:00:00Z',
      latestScoreDocumentId: null,
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
    expect(
      screen.queryByText(
        'This screen confirms that an existing case can be reopened from the case entry page without hitting a 404.'
      )
    ).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: /upload musicxml/i })).toBeDisabled();
    expect(screen.getByRole('button', { name: /edit case/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /reset case/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /return to interview/i })).toHaveAttribute(
      'href',
      '/interview?caseId=existing-case-1&mode=edit'
    );
  });

  it('offers an interview action for in-progress cases', async () => {
    vi.mocked(casesApi.getCase).mockResolvedValue({
      id: 'existing-case-1',
      status: 'interview_in_progress',
      instrumentIdentity: 'trumpet-bb',
      scoreCount: 0,
      createdAt: '2024-01-15T10:00:00Z',
      updatedAt: '2024-01-16T12:00:00Z',
      latestScoreDocumentId: null,
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
      latestScoreDocumentId: null,
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
        latestScoreDocumentId: null,
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
        latestScoreDocumentId: 'score-123',
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
    vi.mocked(scoresApi.getScore).mockResolvedValue({
      scoreDocumentId: 'score-123',
      transpositionCaseId: 'existing-case-1',
      processingStatus: 'recommendation_pending',
      originalFilename: 'example.musicxml',
      safeSummary: 'The score is parsed and ready for recommendation generation.',
      latestTransformationJobId: null,
      sourcePreview: {
        scoreDocumentId: 'score-123',
        artifactRole: 'source',
        availability: 'ready',
        rendererFormat: 'musicxml_preview',
        pageCount: 1,
        revisionToken: '2026-03-20T10:00:00+00:00',
        safeSummary: 'The uploaded score is ready for read-only preview.',
        previewAccess: '/scores/score-123/preview/content?revision=2026-03-20T10:00:00+00:00',
        originalFilename: 'example.musicxml',
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
      resultPreview: {
        scoreDocumentId: 'score-123',
        artifactRole: 'result',
        availability: 'unavailable',
        revisionToken: '2026-03-20T10:00:00+00:00',
        safeSummary: 'A result preview is not available yet because no transformed result artifact exists.',
        originalFilename: 'example.musicxml',
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
    await waitFor(() => {
      expect(scoresApi.getScore).toHaveBeenCalledWith('score-123');
    });
    await waitFor(() => {
      expect(screen.queryByText('Score parsed successfully')).not.toBeInTheDocument();
    });
    expect(screen.queryByText(/Parsed 1 part\(s\) across 1 measure\(s\)\./i)).not.toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /original/i })).toHaveAttribute('aria-selected', 'true');
    expect(screen.getByRole('tab', { name: /result/i })).toBeDisabled();
    expect(screen.getByLabelText('Read-only score preview')).toBeInTheDocument();
    expect(screen.getByLabelText(/score viewer/i)).toBeInTheDocument();
    expect(screen.getByLabelText('Score preview pagination')).toBeInTheDocument();
    expect(screen.getByText('Mocked score viewer')).toBeInTheDocument();
    expect(screen.queryByText(/The uploaded score is ready for read-only preview\./i)).not.toBeInTheDocument();
    expect(screen.queryByText(/^ready$/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/^Parts$/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/^Measures$/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/^Notes$/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/^Rests$/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/ピアノ/i)).not.toBeInTheDocument();
    const actionRow = screen.getByRole('link', { name: /back to cases/i }).closest('div');
    const preview = screen.getByLabelText('Score preview workspace');
    expect(actionRow).not.toBeNull();
    expect(preview.compareDocumentPosition(actionRow as Node) & Node.DOCUMENT_POSITION_PRECEDING).toBeTruthy();
    expect(screen.getByRole('button', { name: /load recommendations/i })).toBeInTheDocument();
  });

  it('renders recommendation cards and allows explicit selection', async () => {
    vi.mocked(casesApi.getCase)
      .mockResolvedValueOnce({
        id: 'existing-case-1',
        status: 'ready_for_upload',
        instrumentIdentity: 'trumpet-bb',
        scoreCount: 0,
        createdAt: '2024-01-15T10:00:00Z',
        updatedAt: '2024-01-16T12:00:00Z',
        latestScoreDocumentId: null,
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
        latestScoreDocumentId: 'score-123',
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
          noteCount: 1,
          restCount: 0,
          parts: [{ partId: 'P1', name: 'Flute' }],
        },
      },
    });
    vi.mocked(scoresApi.getScore)
      .mockResolvedValueOnce({
        scoreDocumentId: 'score-123',
        transpositionCaseId: 'existing-case-1',
        processingStatus: 'recommendation_pending',
        originalFilename: 'example.musicxml',
        safeSummary: 'The score is parsed and ready for recommendation generation.',
        latestTransformationJobId: null,
        sourcePreview: {
          scoreDocumentId: 'score-123',
          artifactRole: 'source',
          availability: 'ready',
          rendererFormat: 'musicxml_preview',
          pageCount: 1,
          revisionToken: '2026-03-20T10:00:00+00:00',
          safeSummary: 'The uploaded score is ready for read-only preview.',
          previewAccess: '/scores/score-123/preview/content?revision=2026-03-20T10:00:00+00:00',
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
        },
        resultPreview: {
          scoreDocumentId: 'score-123',
          artifactRole: 'result',
          availability: 'unavailable',
          revisionToken: '2026-03-20T10:00:00+00:00',
          safeSummary: 'A result preview is not available yet because no transformed result artifact exists.',
          originalFilename: 'example.musicxml',
        },
      })
      .mockResolvedValueOnce({
        scoreDocumentId: 'score-123',
        transpositionCaseId: 'existing-case-1',
        processingStatus: 'completed',
        originalFilename: 'example.musicxml',
        safeSummary: 'The score has a transformed result artifact ready.',
        latestTransformationJobId: 'job-1',
        sourcePreview: {
          scoreDocumentId: 'score-123',
          artifactRole: 'source',
          availability: 'ready',
          rendererFormat: 'musicxml_preview',
          pageCount: 1,
          revisionToken: '2026-03-20T10:00:00+00:00',
          safeSummary: 'The uploaded score is ready for read-only preview.',
          previewAccess: '/scores/score-123/preview/content?revision=2026-03-20T10:00:00+00:00',
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
        },
        resultPreview: {
          scoreDocumentId: 'score-123',
          artifactRole: 'result',
          availability: 'ready',
          rendererFormat: 'musicxml_preview',
          pageCount: 1,
          revisionToken: '2026-03-20T11:00:00+00:00',
          safeSummary: 'A transformed result artifact is ready for read-only preview.',
          previewAccess: '/transformations/job-1/preview/content?revision=2026-03-20T11%3A00%3A00%2B00%3A00',
          originalFilename: 'example-transformed.musicxml',
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
      });
    vi.mocked(recommendationsApi.generateRecommendations).mockResolvedValue({
      status: 'ready',
      transpositionCaseId: 'existing-case-1',
      scoreDocumentId: 'score-123',
      recommendations: [
        {
          recommendationId: 'rec-primary',
          label: 'Primary recommendation',
          targetRange: { min: 'G3', max: 'D5' },
          recommendedKey: 'concert_c',
          confidence: 'medium',
          summaryReason: 'Matches the confirmed player comfort range.',
          warnings: [{ code: 'register_risk', severity: 'warning', message: 'Register risk is present.' }],
          isPrimary: true,
          isStale: false,
        },
        {
          recommendationId: 'rec-secondary',
          label: 'Instrument baseline alternative',
          targetRange: { min: 'C4', max: 'D7' },
          recommendedKey: null,
          confidence: 'low',
          summaryReason: 'Generic baseline alternative.',
          warnings: [],
          isPrimary: false,
          isStale: false,
        },
      ],
      failure: null,
    });
    vi.mocked(transformationsApi.runTransformation).mockResolvedValue({
      transformationJobId: 'job-1',
      status: 'completed',
      transpositionCaseId: 'existing-case-1',
      scoreDocumentId: 'score-123',
      recommendationId: 'rec-primary',
      selectedRangeMin: 'G3',
      selectedRangeMax: 'D5',
      semitoneShift: -2,
      safeSummary: 'The deterministic transformation completed successfully.',
      resultFilename: 'example-transformed.musicxml',
      resultPreviewRevisionToken: '2026-03-20T11:00:00+00:00',
      isRetryable: false,
      failureCode: null,
      failureSeverity: null,
      warnings: [],
      createdAt: '2026-03-20T11:00:00Z',
    });
    vi.mocked(transformationsApi.getTransformation).mockResolvedValue({
      transformationJobId: 'job-1',
      status: 'completed',
      transpositionCaseId: 'existing-case-1',
      scoreDocumentId: 'score-123',
      recommendationId: 'rec-primary',
      selectedRangeMin: 'G3',
      selectedRangeMax: 'D5',
      semitoneShift: -2,
      safeSummary: 'The deterministic transformation completed successfully.',
      resultFilename: 'example-transformed.musicxml',
      resultPreviewRevisionToken: '2026-03-20T11:00:00+00:00',
      isRetryable: false,
      failureCode: null,
      failureSeverity: null,
      warnings: [],
      createdAt: '2026-03-20T11:00:00Z',
    });

    render(<CaseDetailPage />);

    const fileInput = await screen.findByLabelText('MusicXML file');
    const file = new File(['<score-partwise></score-partwise>'], 'example.musicxml', {
      type: 'application/xml',
    });
    fireEvent.change(fileInput, { target: { files: [file] } });
    fireEvent.click(screen.getByRole('button', { name: /upload musicxml/i }));

    expect(await screen.findByRole('button', { name: /load recommendations/i })).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /load recommendations/i }));

    await waitFor(() => {
      expect(recommendationsApi.generateRecommendations).toHaveBeenCalledWith('existing-case-1', 'score-123');
    });

    expect(await screen.findByText('Review and choose a recommendation')).toBeInTheDocument();
    const recommendationWorkspace = screen.getByLabelText('Recommendation review');
    const previewWorkspace = screen.getByLabelText('Score preview workspace');
    expect(previewWorkspace.compareDocumentPosition(recommendationWorkspace) & Node.DOCUMENT_POSITION_PRECEDING).toBeTruthy();
    expect(screen.getByText('Primary recommendation')).toBeInTheDocument();
    expect(screen.getByText('Instrument baseline alternative')).toBeInTheDocument();
    expect(screen.getByText('Register risk is present.')).toBeInTheDocument();

    fireEvent.click(screen.getAllByRole('button', { name: /select recommendation/i })[0]);
    expect(await screen.findByText(/A recommendation is selected for the next transformation step/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /run transformation/i })).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /run transformation/i }));
    await waitFor(() => {
      expect(transformationsApi.runTransformation).toHaveBeenCalledWith(
        'existing-case-1',
        'score-123',
        'rec-primary'
      );
    });
    await waitFor(() => {
      expect(transformationsApi.getTransformation).toHaveBeenCalledWith('job-1');
    });
    expect(await screen.findByText(/The deterministic transformation completed successfully\./i)).toBeInTheDocument();
    expect(await screen.findByRole('tab', { name: /result/i })).toHaveAttribute('aria-selected', 'true');
    expect(screen.getByRole('link', { name: /download result musicxml/i })).toHaveAttribute(
      'href',
      'http://localhost:8000/scores/score-123/download?artifact=result'
    );
  });

  it('renders stale recommendations as blocked until they are regenerated', async () => {
    vi.mocked(casesApi.getCase).mockResolvedValue({
      id: 'existing-case-1',
      status: 'ready_for_upload',
      instrumentIdentity: 'trumpet-bb',
      scoreCount: 1,
      createdAt: '2024-01-15T10:00:00Z',
      updatedAt: '2024-01-16T12:00:00Z',
      latestScoreDocumentId: 'score-123',
      constraints: {
        highest_playable_tone: null,
        lowest_playable_tone: null,
        restricted_tones: [],
        restricted_registers: [],
        difficult_keys: [],
        preferred_keys: [],
        comfort_range_min: 'A3',
        comfort_range_max: 'E5',
      },
    });
    vi.mocked(scoresApi.getScore).mockResolvedValue({
      scoreDocumentId: 'score-123',
      transpositionCaseId: 'existing-case-1',
      processingStatus: 'recommendation_ready',
      originalFilename: 'example.musicxml',
      safeSummary: 'The score is ready for recommendation review.',
      latestTransformationJobId: null,
      sourcePreview: {
        scoreDocumentId: 'score-123',
        artifactRole: 'source',
        availability: 'ready',
        rendererFormat: 'musicxml_preview',
        pageCount: 1,
        revisionToken: '2026-03-20T10:00:00+00:00',
        safeSummary: 'The uploaded score is ready for read-only preview.',
        previewAccess: '/scores/score-123/preview/content?revision=2026-03-20T10:00:00+00:00',
        originalFilename: 'example.musicxml',
      },
      resultPreview: {
        scoreDocumentId: 'score-123',
        artifactRole: 'result',
        availability: 'unavailable',
        revisionToken: '2026-03-20T10:00:00+00:00',
        safeSummary: 'A result preview is not available yet because no transformed result artifact exists.',
        originalFilename: 'example.musicxml',
      },
    });
    vi.mocked(recommendationsApi.getRecommendations).mockResolvedValue({
      status: 'ready',
      transpositionCaseId: 'existing-case-1',
      scoreDocumentId: 'score-123',
      recommendations: [
        {
          recommendationId: 'rec-stale-1',
          label: 'Primary recommendation',
          targetRange: { min: 'G3', max: 'D5' },
          recommendedKey: 'concert_c',
          confidence: 'medium',
          summaryReason: 'Matches the prior confirmed player comfort range.',
          warnings: [],
          isPrimary: true,
          isStale: true,
        },
      ],
      failure: null,
    });

    render(<CaseDetailPage />);

    expect(await screen.findByText('Review and choose a recommendation')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /load recommendations/i })).toBeInTheDocument();
    expect(await screen.findByText(/Recommendation refresh required/i)).toBeInTheDocument();
    expect(screen.getByText(/Stale recommendation\. Regenerate recommendations before transforming\./i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /stale recommendation/i })).toBeDisabled();
    expect(screen.queryByRole('button', { name: /run transformation/i })).not.toBeInTheDocument();
  });

  it('renders a calm failed preview state for an existing uploaded score', async () => {
    vi.mocked(casesApi.getCase).mockResolvedValue({
      id: 'existing-case-1',
      status: 'ready_for_upload',
      instrumentIdentity: 'trumpet-bb',
      scoreCount: 1,
      createdAt: '2024-01-15T10:00:00Z',
      updatedAt: '2024-01-16T12:00:00Z',
      latestScoreDocumentId: 'score-failed',
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
    vi.mocked(scoresApi.getScore).mockResolvedValue({
      scoreDocumentId: 'score-failed',
      transpositionCaseId: 'existing-case-1',
      processingStatus: 'failed',
      originalFilename: 'broken.musicxml',
      safeSummary: 'The score flow failed before a recommendation-ready state was reached.',
      latestTransformationJobId: null,
      sourcePreview: {
        scoreDocumentId: 'score-failed',
        artifactRole: 'source',
        availability: 'failed',
        revisionToken: '2026-03-20T10:00:00+00:00',
        safeSummary: 'The uploaded score could not be prepared for preview.',
        failureCode: 'invalid_xml',
        failureSeverity: 'warning',
        originalFilename: 'broken.musicxml',
        canonicalScoreSummary: null,
      },
      resultPreview: {
        scoreDocumentId: 'score-failed',
        artifactRole: 'result',
        availability: 'unavailable',
        revisionToken: '2026-03-20T10:00:00+00:00',
        safeSummary: 'A result preview is not available yet because no transformed result artifact exists.',
        originalFilename: 'broken.musicxml',
      },
    });

    render(<CaseDetailPage />);

    expect(await screen.findByText(/The uploaded score could not be prepared for preview\./i)).toBeInTheDocument();
    expect(screen.getByText(/Failure type: invalid_xml/i)).toBeInTheDocument();
    expect(screen.queryByText(/local:\/\//i)).not.toBeInTheDocument();
  });

  it('allows loading recommendations for an existing ready preview after reload', async () => {
    vi.mocked(casesApi.getCase).mockResolvedValue({
      id: 'existing-case-1',
      status: 'ready_for_upload',
      instrumentIdentity: 'trumpet-bb',
      scoreCount: 1,
      createdAt: '2024-01-15T10:00:00Z',
      updatedAt: '2024-01-16T12:00:00Z',
      latestScoreDocumentId: 'score-123',
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
    vi.mocked(scoresApi.getScore).mockResolvedValue({
      scoreDocumentId: 'score-123',
      transpositionCaseId: 'existing-case-1',
      processingStatus: 'recommendation_pending',
      originalFilename: 'example.musicxml',
      safeSummary: 'The score is parsed and ready for recommendation generation.',
      latestTransformationJobId: null,
      sourcePreview: {
        scoreDocumentId: 'score-123',
        artifactRole: 'source',
        availability: 'ready',
        rendererFormat: 'musicxml_preview',
        pageCount: 2,
        revisionToken: '2026-03-20T10:00:00+00:00',
        safeSummary: 'The uploaded score is ready for read-only preview.',
        previewAccess: '/scores/score-123/preview/content?revision=2026-03-20T10:00:00+00:00',
        originalFilename: 'example.musicxml',
        canonicalScoreSummary: null,
      },
      resultPreview: {
        scoreDocumentId: 'score-123',
        artifactRole: 'result',
        availability: 'unavailable',
        revisionToken: '2026-03-20T10:00:00+00:00',
        safeSummary: 'A result preview is not available yet because no transformed result artifact exists.',
        originalFilename: 'example.musicxml',
      },
    });
    vi.mocked(recommendationsApi.generateRecommendations).mockResolvedValue({
      status: 'ready',
      transpositionCaseId: 'existing-case-1',
      scoreDocumentId: 'score-123',
      recommendations: [],
      failure: null,
    });

    render(<CaseDetailPage />);

    expect(await screen.findByRole('button', { name: /load recommendations/i })).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /load recommendations/i }));

    await waitFor(() => {
      expect(recommendationsApi.generateRecommendations).toHaveBeenCalledWith('existing-case-1', 'score-123');
    });
  });

  it('reloads the latest persisted transformation status for an existing score', async () => {
    vi.mocked(casesApi.getCase).mockResolvedValue({
      id: 'existing-case-1',
      status: 'ready_for_upload',
      instrumentIdentity: 'trumpet-bb',
      scoreCount: 1,
      createdAt: '2024-01-15T10:00:00Z',
      updatedAt: '2024-01-16T12:00:00Z',
      latestScoreDocumentId: 'score-123',
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
    vi.mocked(scoresApi.getScore).mockResolvedValue({
      scoreDocumentId: 'score-123',
      transpositionCaseId: 'existing-case-1',
      processingStatus: 'completed',
      originalFilename: 'example.musicxml',
      safeSummary: 'The score has a transformed result artifact ready.',
      latestTransformationJobId: 'job-1',
      sourcePreview: {
        scoreDocumentId: 'score-123',
        artifactRole: 'source',
        availability: 'ready',
        rendererFormat: 'musicxml_preview',
        pageCount: 1,
        revisionToken: '2026-03-20T10:00:00+00:00',
        safeSummary: 'The uploaded score is ready for read-only preview.',
        previewAccess: '/scores/score-123/preview/content?revision=2026-03-20T10:00:00+00:00',
        originalFilename: 'example.musicxml',
        canonicalScoreSummary: null,
      },
      resultPreview: {
        scoreDocumentId: 'score-123',
        artifactRole: 'result',
        availability: 'ready',
        rendererFormat: 'musicxml_preview',
        pageCount: 1,
        revisionToken: '2026-03-20T11:00:00+00:00',
        safeSummary: 'A transformed result artifact is ready for read-only preview.',
        previewAccess: '/transformations/job-1/preview/content?revision=2026-03-20T11%3A00%3A00%2B00%3A00',
        originalFilename: 'example-transformed.musicxml',
        canonicalScoreSummary: null,
      },
    });
    vi.mocked(transformationsApi.getTransformation).mockResolvedValue({
      transformationJobId: 'job-1',
      status: 'completed',
      transpositionCaseId: 'existing-case-1',
      scoreDocumentId: 'score-123',
      recommendationId: 'rec-primary',
      selectedRangeMin: 'G3',
      selectedRangeMax: 'D5',
      semitoneShift: -2,
      safeSummary: 'The deterministic transformation completed successfully.',
      resultFilename: 'example-transformed.musicxml',
      resultPreviewRevisionToken: '2026-03-20T11:00:00+00:00',
      isRetryable: false,
      failureCode: null,
      failureSeverity: null,
      warnings: [],
      createdAt: '2026-03-20T11:00:00Z',
    });

    render(<CaseDetailPage />);

    await waitFor(() => {
      expect(transformationsApi.getTransformation).toHaveBeenCalledWith('job-1');
    });
    expect(await screen.findByText(/The deterministic transformation completed successfully\./i)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /download result musicxml/i })).toHaveAttribute(
      'href',
      'http://localhost:8000/scores/score-123/download?artifact=result'
    );
  });

  it('keeps the case page visible when only the transformation status load fails', async () => {
    vi.mocked(casesApi.getCase).mockResolvedValue({
      id: 'existing-case-1',
      status: 'ready_for_upload',
      instrumentIdentity: 'trumpet-bb',
      scoreCount: 1,
      createdAt: '2024-01-15T10:00:00Z',
      updatedAt: '2024-01-16T12:00:00Z',
      latestScoreDocumentId: 'score-123',
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
    vi.mocked(scoresApi.getScore).mockResolvedValue({
      scoreDocumentId: 'score-123',
      transpositionCaseId: 'existing-case-1',
      processingStatus: 'completed',
      originalFilename: 'example.musicxml',
      safeSummary: 'The score has a transformed result artifact ready.',
      latestTransformationJobId: 'job-1',
      sourcePreview: {
        scoreDocumentId: 'score-123',
        artifactRole: 'source',
        availability: 'ready',
        rendererFormat: 'musicxml_preview',
        pageCount: 1,
        revisionToken: '2026-03-20T10:00:00+00:00',
        safeSummary: 'The uploaded score is ready for read-only preview.',
        previewAccess: '/scores/score-123/preview/content?revision=2026-03-20T10:00:00+00:00',
        originalFilename: 'example.musicxml',
        canonicalScoreSummary: null,
      },
      resultPreview: {
        scoreDocumentId: 'score-123',
        artifactRole: 'result',
        availability: 'ready',
        rendererFormat: 'musicxml_preview',
        pageCount: 1,
        revisionToken: '2026-03-20T11:00:00+00:00',
        safeSummary: 'A transformed result artifact is ready for read-only preview.',
        previewAccess: '/transformations/job-1/preview/content?revision=2026-03-20T11%3A00%3A00%2B00%3A00',
        originalFilename: 'example-transformed.musicxml',
        canonicalScoreSummary: null,
      },
    });
    vi.mocked(transformationsApi.getTransformation).mockRejectedValue(new Error('transformation read endpoint down'));

    render(<CaseDetailPage />);

    expect(await screen.findByText('Case overview')).toBeInTheDocument();
    expect(await screen.findByText(/Could not load the transformation status/i)).toBeInTheDocument();
    expect(screen.getByText('trumpet-bb')).toBeInTheDocument();
    expect(screen.queryByText(/Could not load the selected case/i)).not.toBeInTheDocument();
  });

  it('keeps the case overview visible when only the preview load fails', async () => {
    vi.mocked(casesApi.getCase).mockResolvedValue({
      id: 'existing-case-1',
      status: 'ready_for_upload',
      instrumentIdentity: 'trumpet-bb',
      scoreCount: 1,
      createdAt: '2024-01-15T10:00:00Z',
      updatedAt: '2024-01-16T12:00:00Z',
      latestScoreDocumentId: 'score-123',
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
    vi.mocked(scoresApi.getScore).mockRejectedValue(new Error('preview endpoint down'));

    render(<CaseDetailPage />);

    expect(await screen.findByText('Case overview')).toBeInTheDocument();
    expect(await screen.findByText(/Could not load the score preview/i)).toBeInTheDocument();
    expect(screen.getByText('trumpet-bb')).toBeInTheDocument();
    expect(screen.queryByText(/Could not load the selected case/i)).not.toBeInTheDocument();
  });

  it('allows editing the case constraints directly on the case page', async () => {
    vi.mocked(casesApi.getCase).mockResolvedValue({
      id: 'existing-case-1',
      status: 'ready_for_upload',
      instrumentIdentity: 'trumpet-bb',
      scoreCount: 0,
      createdAt: '2024-01-15T10:00:00Z',
      updatedAt: '2024-01-16T12:00:00Z',
      latestScoreDocumentId: null,
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
    vi.mocked(casesApi.updateCase).mockResolvedValue({
      id: 'existing-case-1',
      status: 'ready_for_upload',
      instrumentIdentity: 'flute',
      scoreCount: 0,
      createdAt: '2024-01-15T10:00:00Z',
      updatedAt: '2024-01-16T12:30:00Z',
      latestScoreDocumentId: null,
      constraints: {
        highest_playable_tone: null,
        lowest_playable_tone: null,
        restricted_tones: [],
        restricted_registers: [],
        difficult_keys: [],
        preferred_keys: [],
        comfort_range_min: 'A3',
        comfort_range_max: 'E5',
      },
    });

    render(<CaseDetailPage />);

    fireEvent.click(await screen.findByRole('button', { name: /^edit case$/i }));
    fireEvent.change(screen.getByLabelText(/instrument identity/i), { target: { value: 'flute' } });
    fireEvent.change(screen.getByLabelText(/comfort range min/i), { target: { value: 'A3' } });
    fireEvent.change(screen.getByLabelText(/comfort range max/i), { target: { value: 'E5' } });
    fireEvent.click(screen.getByRole('button', { name: /save case changes/i }));

    await waitFor(() => {
      expect(casesApi.updateCase).toHaveBeenCalledWith('existing-case-1', {
        instrumentIdentity: 'flute',
        constraints: {
          highest_playable_tone: null,
          lowest_playable_tone: null,
          restricted_tones: [],
          restricted_registers: [],
          difficult_keys: [],
          preferred_keys: [],
          comfort_range_min: 'A3',
          comfort_range_max: 'E5',
        },
      });
    });
    expect(await screen.findByText('flute')).toBeInTheDocument();
  });

  it('resets the case explicitly and clears the current workflow state', async () => {
    vi.mocked(casesApi.getCase).mockResolvedValue({
      id: 'existing-case-1',
      status: 'ready_for_upload',
      instrumentIdentity: 'trumpet-bb',
      scoreCount: 1,
      createdAt: '2024-01-15T10:00:00Z',
      updatedAt: '2024-01-16T12:00:00Z',
      latestScoreDocumentId: 'score-123',
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
    vi.mocked(casesApi.resetCase).mockResolvedValue({
      id: 'existing-case-1',
      status: 'new',
      instrumentIdentity: 'trumpet-bb',
      scoreCount: 0,
      createdAt: '2024-01-15T10:00:00Z',
      updatedAt: '2024-01-16T12:30:00Z',
      latestScoreDocumentId: null,
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
    vi.mocked(scoresApi.getScore).mockResolvedValue({
      scoreDocumentId: 'score-123',
      transpositionCaseId: 'existing-case-1',
      processingStatus: 'recommendation_pending',
      originalFilename: 'example.musicxml',
      safeSummary: 'The score is parsed and ready for recommendation generation.',
      latestTransformationJobId: null,
      sourcePreview: {
        scoreDocumentId: 'score-123',
        artifactRole: 'source',
        availability: 'ready',
        rendererFormat: 'musicxml_preview',
        pageCount: 1,
        revisionToken: '2026-03-20T10:00:00+00:00',
        safeSummary: 'The uploaded score is ready for read-only preview.',
        previewAccess: '/scores/score-123/preview/content?revision=2026-03-20T10:00:00+00:00',
        originalFilename: 'example.musicxml',
        canonicalScoreSummary: null,
      },
      resultPreview: {
        scoreDocumentId: 'score-123',
        artifactRole: 'result',
        availability: 'unavailable',
        revisionToken: '2026-03-20T10:00:00+00:00',
        safeSummary: 'A result preview is not available yet because no transformed result artifact exists.',
        originalFilename: 'example.musicxml',
      },
    });

    render(<CaseDetailPage />);

    fireEvent.click(await screen.findByRole('button', { name: /reset case/i }));

    await waitFor(() => {
      expect(casesApi.resetCase).toHaveBeenCalledWith('existing-case-1');
    });
    expect(await screen.findByRole('link', { name: /begin interview/i })).toHaveAttribute(
      'href',
      '/interview?caseId=existing-case-1'
    );
  });
});
