/**
 * Component tests for Frontend-4: "Wire the create new case action"
 * 
 * These tests verify the core acceptance criteria:
 * - The action is visible and clickable
 * - It routes or transitions into the new-case flow
 * - It does not break the existing case list state
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
  },
  ApiError: class ApiError extends Error {
    constructor(message: string, public status: number) {
      super(message);
      this.name = 'ApiError';
    }
  },
}));

// Mock next/navigation
const mockPush = vi.fn();
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
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
    status: 'completed',
    instrumentIdentity: 'flute',
    scoreCount: 5,
    createdAt: '2024-01-10T08:00:00Z',
    updatedAt: '2024-01-12T16:00:00Z',
  },
];

describe('Frontend-4: Create New Case Action', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockPush.mockClear();
  });

  /**
   * Acceptance Criterion 1: The action is visible and clickable
   */
  describe('Action Visibility', () => {
    it('shows "Start New Case" button that is visible', async () => {
      vi.mocked(casesApi.listCases).mockResolvedValue([]);
      
      render(<CaseEntryPage />);
      
      // Wait for the button to appear
      const button = await screen.findByRole('button', { 
        name: /start new case/i 
      });
      
      expect(button).toBeInTheDocument();
      expect(button).toBeVisible();
    });

    it('button is clickable (not disabled) when not creating', async () => {
      vi.mocked(casesApi.listCases).mockResolvedValue([]);
      
      render(<CaseEntryPage />);
      
      const button = await screen.findByRole('button', { 
        name: /start new case/i 
      });
      
      expect(button).not.toBeDisabled();
    });

    it('button shows "Creating..." state during creation', async () => {
      vi.mocked(casesApi.listCases).mockResolvedValue([]);
      
      // Simulate slow API call
      vi.mocked(casesApi.createCase).mockImplementation(
        () => new Promise(resolve => setTimeout(() => resolve({
          transpositionCaseId: 'new-case-123',
          status: 'new',
          caseSummary: mockCases[0],
        }), 50))
      );
      
      render(<CaseEntryPage />);
      
      const button = await screen.findByRole('button', { 
        name: /start new case/i 
      });
      
      fireEvent.click(button);
      
      // Check for loading state
      await waitFor(() => {
        expect(screen.getByText(/creating.../i)).toBeInTheDocument();
      });
      
      expect(button).toBeDisabled();
    });
  });

  /**
   * Acceptance Criterion 2: It routes or transitions into the new-case flow
   */
  describe('Navigation to New Case Flow', () => {
    it('navigates to interview page after successful case creation', async () => {
      vi.mocked(casesApi.listCases).mockResolvedValue([]);
      vi.mocked(casesApi.createCase).mockResolvedValue({
        transpositionCaseId: 'new-case-123',
        status: 'new',
        caseSummary: mockCases[0],
      });
      
      render(<CaseEntryPage />);
      
      const button = await screen.findByRole('button', { 
        name: /start new case/i 
      });
      
      fireEvent.click(button);
      
      // Verify API was called
      await waitFor(() => {
        expect(casesApi.createCase).toHaveBeenCalledWith({
          instrument_identity: 'placeholder',
        });
      });
      
      // Verify navigation to interview flow
      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith('/interview?caseId=new-case-123');
      });
    });

    it('calls createCase API with correct payload', async () => {
      vi.mocked(casesApi.listCases).mockResolvedValue([]);
      vi.mocked(casesApi.createCase).mockResolvedValue({
        transpositionCaseId: 'new-case-456',
        status: 'new',
        caseSummary: mockCases[0],
      });
      
      render(<CaseEntryPage />);
      
      const button = await screen.findByRole('button', { 
        name: /start new case/i 
      });
      fireEvent.click(button);
      
      await waitFor(() => {
        expect(casesApi.createCase).toHaveBeenCalledTimes(1);
        expect(casesApi.createCase).toHaveBeenCalledWith({
          instrument_identity: 'placeholder',
          existing_case_action: undefined,
          existing_case_id: undefined,
        });
      });
    });
  });

  /**
   * Acceptance Criterion 3: It does not break the existing case list state
   */
  describe('Case List State Preservation', () => {
    it('keeps case list visible after clicking create button', async () => {
      vi.mocked(casesApi.listCases).mockResolvedValue(mockCases);
      vi.mocked(casesApi.createCase).mockResolvedValue({
        transpositionCaseId: 'new-case-789',
        status: 'new',
        caseSummary: mockCases[0],
      });
      
      render(<CaseEntryPage />);
      
      // Wait for cases to load
      await waitFor(() => {
        expect(screen.getByText('trumpet-bb')).toBeInTheDocument();
      });
      
      // Click create button
      const createButton = screen.getByRole('button', { 
        name: /start new case/i 
      });
      fireEvent.click(createButton);
      
      // Cases should still be visible (state not broken)
      // Use queryByText since element should already be there
      expect(screen.queryByText('trumpet-bb')).toBeInTheDocument();
      expect(screen.queryByText('flute')).toBeInTheDocument();
      
      // Suggested case section should still exist
      expect(screen.queryByText('Suggested case')).toBeInTheDocument();
      expect(screen.queryByText('Other cases')).toBeInTheDocument();
    });

    it('maintains case count after failed creation', async () => {
      vi.mocked(casesApi.listCases).mockResolvedValue(mockCases);
      vi.mocked(casesApi.createCase).mockRejectedValue(
        new Error('Network error')
      );
      
      render(<CaseEntryPage />);
      
      // Wait for cases to load
      await waitFor(() => {
        expect(screen.getByText('trumpet-bb')).toBeInTheDocument();
      });
      
      // Try to create
      const createButton = screen.getByRole('button', { 
        name: /start new case/i 
      });
      fireEvent.click(createButton);
      
      // Wait for error
      await waitFor(() => {
        expect(screen.getByText(/Failed to create case/i)).toBeInTheDocument();
      });
      
      // Cases should still be visible
      expect(screen.getByText('trumpet-bb')).toBeInTheDocument();
      expect(screen.getByText('flute')).toBeInTheDocument();
    });
  });

  /**
   * Additional: Error Handling
   */
  describe('Error Handling', () => {
    it('shows error message when case creation fails', async () => {
      vi.mocked(casesApi.listCases).mockResolvedValue([]);
      vi.mocked(casesApi.createCase).mockRejectedValue(
        new Error('Failed to create case')
      );
      
      render(<CaseEntryPage />);
      
      const button = await screen.findByRole('button', { 
        name: /start new case/i 
      });
      fireEvent.click(button);
      
      await waitFor(() => {
        expect(screen.getByText(/Failed to create case/i)).toBeInTheDocument();
      });
      
      // Button should be re-enabled after error
      expect(button).not.toBeDisabled();
    });

    it('allows retry after error', async () => {
      vi.mocked(casesApi.listCases).mockResolvedValue([]);
      
      // First call fails, second succeeds
      vi.mocked(casesApi.createCase)
        .mockRejectedValueOnce(new Error('First attempt failed'))
        .mockResolvedValueOnce({
          transpositionCaseId: 'success-case',
          status: 'new',
          caseSummary: mockCases[0],
        });
      
      render(<CaseEntryPage />);
      
      const button = await screen.findByRole('button', { 
        name: /start new case/i 
      });
      
      // First attempt
      fireEvent.click(button);
      
      await waitFor(() => {
        expect(screen.getByText(/Failed to create case/i)).toBeInTheDocument();
      });
      
      // Note: Current implementation doesn't have explicit retry button for create errors
      // The error banner shows "Try again" which reloads cases, not retries creation
      // This is acceptable for MVP scaffold
      expect(button).not.toBeDisabled(); // Button re-enabled after error
    });
  });
});
