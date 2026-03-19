import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import NewCaseFlowPage from './page';

let currentSearchParams = new URLSearchParams({
  caseId: 'case-123',
});

vi.mock('next/navigation', () => ({
  useSearchParams: () => currentSearchParams,
}));

describe('NewCaseFlowPage', () => {
  beforeEach(() => {
    currentSearchParams = new URLSearchParams({
      caseId: 'case-123',
    });
  });

  it('offers the Start Interview path when a caseId is present', () => {
    render(<NewCaseFlowPage />);

    expect(screen.getByRole('link', { name: /start interview/i })).toHaveAttribute(
      'href',
      '/interview?caseId=case-123'
    );
  });

  it('hides the Start Interview path when no caseId is present', () => {
    currentSearchParams = new URLSearchParams();

    render(<NewCaseFlowPage />);

    expect(screen.queryByRole('link', { name: /start interview/i })).not.toBeInTheDocument();
  });
});
