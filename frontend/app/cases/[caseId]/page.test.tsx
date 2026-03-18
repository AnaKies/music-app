import { render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import CaseDetailPage from './page';
import { casesApi } from '@/shared/api/cases';

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
  });
});
