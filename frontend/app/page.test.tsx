/**
 * Component tests for Case Entry page (Frontend-4).
 * 
 * Tests verify:
 * - Case list rendering
 * - "Create New Case" action visibility and functionality
 * - Loading and error states
 * - Navigation behavior
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import CaseEntryPage from '../app/page';
import { casesApi } from '@/shared/api/cases';
import type { CaseSummary } from '@/shared/types/cases';

// Mock the API client
vi.mock('@/shared/api/cases', () => ({
  casesApi: {
    listCases: vi.fn(),
    createCase: vi.fn(),
    deleteCase: vi.fn(),
  },
  ApiError: class ApiError extends Error {
    constructor(message: string, public status: number) {
      super(message);
      this.name = 'ApiError';
    }
  },
}));

// Mock next/navigation
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: vi.fn(),
  }),
}));

const mockCases: CaseSummary[] = [
  {
    id: 'case-1',
    status: 'ready_for_upload',
    instrumentIdentity: 'trumpet-bb',
    scoreCount: 2,
    createdAt: '2024-01-15T10:00:00Z',
    updatedAt: '2024-01-15T12:00:00Z',
  },
  {
    id: 'case-2',
    status: 'interview_in_progress',
    instrumentIdentity: 'alto-sax-eb',
    scoreCount: 0,
    createdAt: '2024-01-14T09:00:00Z',
    updatedAt: '2024-01-14T09:30:00Z',
  },
  {
    id: 'case-3',
    status: 'completed',
    instrumentIdentity: 'flute',
    scoreCount: 5,
    createdAt: '2024-01-10T08:00:00Z',
    updatedAt: '2024-01-12T16:00:00Z',
  },
];

describe('CaseEntryPage (Frontend-4)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Initial Render', () => {
    it('renders the page header', () => {
      vi.mocked(casesApi.listCases).mockResolvedValue([]);
      
      render(<CaseEntryPage />);
      
      expect(screen.getByText('F1 · Case Entry')).toBeInTheDocument();
      expect(screen.getByText(/Choose a case or start a new transposition flow/i)).toBeInTheDocument();
    });
  });

  describe('Case List Display', () => {
    it('renders cases from API', async () => {
      vi.mocked(casesApi.listCases).mockResolvedValue(mockCases);
      
      render(<CaseEntryPage />);
      
      await waitFor(() => {
        expect(screen.getByText('trumpet-bb')).toBeInTheDocument();
        expect(screen.getByText('alto-sax-eb')).toBeInTheDocument();
        expect(screen.getByText('flute')).toBeInTheDocument();
      });
    });

    it('highlights suggested case (ready_for_upload or interview_in_progress)', async () => {
      vi.mocked(casesApi.listCases).mockResolvedValue(mockCases);
      
      render(<CaseEntryPage />);
      
      await waitFor(() => {
        const suggestedSection = screen.getByText('Suggested case').closest('section');
        expect(suggestedSection).toContainElement(screen.getByText('trumpet-bb'));
      });
    });

    it('shows empty state when no cases exist', async () => {
      vi.mocked(casesApi.listCases).mockResolvedValue([]);
      
      render(<CaseEntryPage />);
      
      await waitFor(() => {
        expect(screen.getByText('No suggested case')).toBeInTheDocument();
      });
    });

    it('displays case status badges', async () => {
      vi.mocked(casesApi.listCases).mockResolvedValue(mockCases);
      
      render(<CaseEntryPage />);
      
      await waitFor(() => {
        expect(screen.getByText('Ready')).toBeInTheDocument();
        expect(screen.getByText('Interview')).toBeInTheDocument();
        expect(screen.getByText('Completed')).toBeInTheDocument();
      });
    });

    it('shows score count for each case', async () => {
      vi.mocked(casesApi.listCases).mockResolvedValue(mockCases);
      
      render(<CaseEntryPage />);
      
      await waitFor(() => {
        expect(screen.getByText('2 scores')).toBeInTheDocument();
        expect(screen.getByText('5 scores')).toBeInTheDocument();
      });
    });

    it('shows a stable short case identifier for otherwise similar cases', async () => {
      vi.mocked(casesApi.listCases).mockResolvedValue([
        {
          id: 'case-abcdef',
          status: 'new',
          instrumentIdentity: 'placeholder',
          scoreCount: 0,
          createdAt: '2024-01-15T10:00:00Z',
          updatedAt: '2024-01-15T12:00:00Z',
        },
      ]);

      render(<CaseEntryPage />);

      await waitFor(() => {
        expect(screen.getByText('Untitled case')).toBeInTheDocument();
        expect(screen.getByText('Case ABCDEF')).toBeInTheDocument();
      });
    });
  });

  describe('Create New Case Action (Frontend-4 Core)', () => {
    it('shows visible and clickable "Start New Case" button', async () => {
      vi.mocked(casesApi.listCases).mockResolvedValue([]);
      
      render(<CaseEntryPage />);
      
      await waitFor(() => {
        const createButton = screen.getByRole('button', { name: /start new case/i });
        expect(createButton).toBeInTheDocument();
        expect(createButton).not.toBeDisabled();
      });
    });

    it('navigates to new case flow on button click', async () => {
      vi.mocked(casesApi.listCases).mockResolvedValue([]);
      vi.mocked(casesApi.createCase).mockResolvedValue({
        transpositionCaseId: 'new-case-123',
        status: 'new',
        caseSummary: mockCases[0],
      });
      
      render(<CaseEntryPage />);
      
      await waitFor(() => {
        const createButton = screen.getByRole('button', { name: /start new case/i });
        fireEvent.click(createButton);
      });
      
      // Verify API call was made
      await waitFor(() => {
        expect(casesApi.createCase).toHaveBeenCalledWith({
          instrument_identity: 'placeholder',
        });
      });
    });

    it('shows loading state during case creation', async () => {
      vi.mocked(casesApi.listCases).mockResolvedValue([]);
      vi.mocked(casesApi.createCase).mockImplementation(
        () => new Promise(resolve => setTimeout(() => resolve({
          transpositionCaseId: 'new-case-123',
          status: 'new',
          caseSummary: mockCases[0],
        }), 100))
      );
      
      render(<CaseEntryPage />);
      
      await waitFor(() => {
        const createButton = screen.getByRole('button', { name: /start new case/i });
        fireEvent.click(createButton);
      });
      
      // Should show "Creating..." text
      await waitFor(() => {
        expect(screen.getByText(/creating.../i)).toBeInTheDocument();
      });
    });

    it('does not break case list state when creating', async () => {
      vi.mocked(casesApi.listCases).mockResolvedValue(mockCases);
      vi.mocked(casesApi.createCase).mockResolvedValue({
        transpositionCaseId: 'new-case-123',
        status: 'new',
        caseSummary: mockCases[0],
      });
      
      render(<CaseEntryPage />);
      
      // Wait for cases to load
      await waitFor(() => {
        expect(screen.getByText('trumpet-bb')).toBeInTheDocument();
      });
      
      // Click create button
      const createButton = screen.getByRole('button', { name: /start new case/i });
      fireEvent.click(createButton);
      
      // Cases should still be visible (state not broken)
      expect(screen.getByText('trumpet-bb')).toBeInTheDocument();
      expect(screen.getByText('alto-sax-eb')).toBeInTheDocument();
    });
  });

  describe('Error Handling', () => {
    it('shows error banner when API call fails', async () => {
      vi.mocked(casesApi.listCases).mockRejectedValue(
        new Error('Network error')
      );
      
      render(<CaseEntryPage />);
      
      await waitFor(() => {
        expect(screen.getByText(/Failed to load cases/i)).toBeInTheDocument();
      });
    });

    it('shows retry option after error', async () => {
      vi.mocked(casesApi.listCases).mockRejectedValue(
        new Error('Network error')
      );
      
      render(<CaseEntryPage />);
      
      await waitFor(() => {
        const retryButton = screen.getByText('Try again');
        expect(retryButton).toBeInTheDocument();
      });
    });

    it('handles API error with status code', async () => {
      const apiError = new Error('Failed to create case');
      (apiError as any).status = 500;
      
      vi.mocked(casesApi.listCases).mockResolvedValue([]);
      vi.mocked(casesApi.createCase).mockRejectedValue(apiError);
      
      render(<CaseEntryPage />);
      
      await waitFor(() => {
        const createButton = screen.getByRole('button', { name: /start new case/i });
        fireEvent.click(createButton);
      });
      
      await waitFor(() => {
        expect(screen.getByText(/Failed to create case/i)).toBeInTheDocument();
      });
    });
  });

  describe('Case Selection', () => {
    it('renders case cards as clickable elements', async () => {
      vi.mocked(casesApi.listCases).mockResolvedValue(mockCases);
      
      render(<CaseEntryPage />);
      
      await waitFor(() => {
        const caseCard = screen.getByText('trumpet-bb').closest('article');
        expect(caseCard).toBeInTheDocument();
      });
    });

    it('shows a provisional delete action only for other cases and removes the deleted case from the list', async () => {
      vi.mocked(casesApi.listCases).mockResolvedValue(mockCases);
      vi.mocked(casesApi.deleteCase).mockResolvedValue(undefined);

      render(<CaseEntryPage />);

      await waitFor(() => {
        expect(screen.getByText('trumpet-bb')).toBeInTheDocument();
      });

      const deleteButtons = screen.getAllByRole('button', { name: /delete case/i });
      expect(deleteButtons).toHaveLength(2);
      expect(screen.queryByRole('button', { name: /delete case trumpet-bb/i })).not.toBeInTheDocument();

      fireEvent.click(screen.getByRole('button', { name: /delete case alto-sax-eb/i }));

      await waitFor(() => {
        expect(casesApi.deleteCase).toHaveBeenCalledWith('case-2');
      });

      expect(screen.queryByText('alto-sax-eb')).not.toBeInTheDocument();
      expect(screen.getByText('trumpet-bb')).toBeInTheDocument();
    });
  });
});
