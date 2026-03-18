/**
 * Test-3: UI test for default-case selection behavior.
 *
 * Verifies:
 * - the suggested case follows the most recently updated non-archived active case rule
 * - the suggested case is semantically marked for assistive technology
 * - archived-only and empty states do not fabricate a suggestion
 * - the suggested case and "Start New Case" button trigger different routes
 */

import { beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';

import CaseEntryPage from './page';
import { casesApi } from '@/shared/api/cases';
import type { CaseSummary } from '@/shared/types/cases';

vi.mock('@/shared/api/cases', () => ({
  casesApi: {
    listCases: vi.fn(),
    createCase: vi.fn(),
  },
  ApiError: class ApiError extends Error {
    constructor(message: string, public status: number) {
      super(message);
      this.name = 'ApiError';
    }
  },
}));

const push = vi.fn();

vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push,
  }),
}));

const activeCasesWithDifferentDates: CaseSummary[] = [
  {
    id: 'case-ready-older',
    status: 'ready_for_upload',
    instrumentIdentity: 'trumpet-bb',
    scoreCount: 2,
    createdAt: '2024-01-15T10:00:00Z',
    updatedAt: '2024-01-15T12:00:00Z',
  },
  {
    id: 'case-interview-newest',
    status: 'interview_in_progress',
    instrumentIdentity: 'alto-sax-eb',
    scoreCount: 0,
    createdAt: '2024-01-14T09:00:00Z',
    updatedAt: '2024-01-16T09:30:00Z',
  },
  {
    id: 'case-completed-middle',
    status: 'completed',
    instrumentIdentity: 'flute',
    scoreCount: 5,
    createdAt: '2024-01-10T08:00:00Z',
    updatedAt: '2024-01-15T16:00:00Z',
  },
  {
    id: 'case-archived-newest',
    status: 'archived',
    instrumentIdentity: 'clarinet-bb',
    scoreCount: 1,
    createdAt: '2024-01-17T08:00:00Z',
    updatedAt: '2024-01-17T18:00:00Z',
  },
];

describe('Test-3: CaseEntryPage default-case selection behavior', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    push.mockReset();
  });

  it('suggests the most recently updated non-archived active case and keeps the others available', async () => {
    vi.mocked(casesApi.listCases).mockResolvedValue(activeCasesWithDifferentDates);

    render(<CaseEntryPage />);

    const suggestedCard = await screen.findByLabelText('Suggested case: alto-sax-eb');
    const suggestedSection = screen.getByText('Suggested case').closest('section');
    const otherCasesSection = screen.getByText('Other cases').closest('section');

    expect(suggestedSection).not.toBeNull();
    expect(otherCasesSection).not.toBeNull();
    expect(within(suggestedSection as HTMLElement).getByLabelText('Suggested case: alto-sax-eb')).toBe(suggestedCard);

    expect(within(otherCasesSection as HTMLElement).getByLabelText('Case: trumpet-bb')).toBeInTheDocument();
    expect(within(otherCasesSection as HTMLElement).getByLabelText('Case: flute')).toBeInTheDocument();
    expect(within(otherCasesSection as HTMLElement).getByLabelText('Case: clarinet-bb')).toBeInTheDocument();
  });

  it('does not fabricate a suggested case when only archived cases exist', async () => {
    vi.mocked(casesApi.listCases).mockResolvedValue([
      {
        id: 'archived-1',
        status: 'archived',
        instrumentIdentity: 'bassoon',
        scoreCount: 1,
        createdAt: '2024-01-13T10:00:00Z',
        updatedAt: '2024-01-15T12:00:00Z',
      },
    ]);

    render(<CaseEntryPage />);

    const suggestedSection = screen.getByText('Suggested case').closest('section');
    const otherCasesSection = await waitFor(() => screen.getByText('Other cases').closest('section'));

    expect(within(suggestedSection as HTMLElement).getByText('No suggested case')).toBeInTheDocument();
    expect(within(otherCasesSection as HTMLElement).getByLabelText('Case: bassoon')).toBeInTheDocument();
  });

  it('handles the empty state without crashing and without rendering a suggested case', async () => {
    vi.mocked(casesApi.listCases).mockResolvedValue([]);

    render(<CaseEntryPage />);

    const suggestedSection = await waitFor(() => screen.getByText('Suggested case').closest('section'));
    const otherCasesSection = screen.getByText('Other cases').closest('section');

    expect(within(suggestedSection as HTMLElement).getByText('No suggested case')).toBeInTheDocument();
    expect(within(otherCasesSection as HTMLElement).getByText('No other cases')).toBeInTheDocument();
  });

  it('routes suggested-case click differently from the new-case button', async () => {
    vi.mocked(casesApi.listCases).mockResolvedValue(activeCasesWithDifferentDates);
    vi.mocked(casesApi.createCase).mockResolvedValue({
      transpositionCaseId: 'new-case-id',
      status: 'new',
      caseSummary: {
        id: 'new-case-id',
        status: 'new',
        instrumentIdentity: 'placeholder',
        scoreCount: 0,
        createdAt: '2024-01-18T10:00:00Z',
        updatedAt: '2024-01-18T10:00:00Z',
      },
    });

    render(<CaseEntryPage />);

    const suggestedCard = await screen.findByLabelText('Suggested case: alto-sax-eb');
    fireEvent.click(suggestedCard);

    expect(push).toHaveBeenCalledWith('/cases/case-interview-newest');

    fireEvent.click(screen.getByRole('button', { name: 'Start New Case' }));

    await waitFor(() => {
      expect(casesApi.createCase).toHaveBeenCalledWith({
        instrument_identity: 'placeholder',
      });
    });
    expect(push).toHaveBeenCalledWith('/interview?caseId=new-case-id');
  });
});
