'use client';

import { useState, useCallback, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { PlusCircle, Music, Clock, Loader2, AlertCircle, Trash2 } from 'lucide-react';
import { casesApi, ApiError } from '@/shared/api/cases';
import type { CaseSummary, CaseStatus } from '@/shared/types/cases';

function sortCasesByUpdatedAtDesc(caseSummaries: CaseSummary[]): CaseSummary[] {
  return [...caseSummaries].sort((leftCase, rightCase) => {
    return new Date(rightCase.updatedAt).getTime() - new Date(leftCase.updatedAt).getTime();
  });
}

function getSuggestedCase(caseSummaries: CaseSummary[]): CaseSummary | null {
  const activeCases = caseSummaries.filter(
    (caseSummary) =>
      caseSummary.status !== 'archived' &&
      (caseSummary.status === 'interview_in_progress' ||
        caseSummary.status === 'ready_for_upload' ||
        caseSummary.status === 'recommendation_ready' ||
        caseSummary.status === 'completed')
  );

  if (activeCases.length === 0) {
    return null;
  }

  return sortCasesByUpdatedAtDesc(activeCases)[0];
}

function getCaseDisplayName(caseSummary: CaseSummary): string {
  if (caseSummary.instrumentIdentity === 'placeholder') {
    return 'Untitled case';
  }

  return caseSummary.instrumentIdentity;
}

function getCaseShortId(caseId: string): string {
  return caseId.slice(-6).toUpperCase();
}

/**
 * Status badge component for case status display.
 */
function StatusBadge({ status }: { status: CaseStatus }) {
  const statusStyles: Record<CaseStatus, string> = {
    new: 'bg-slate-100 text-slate-700',
    interview_in_progress: 'bg-blue-100 text-blue-700',
    ready_for_upload: 'bg-green-100 text-green-700',
    recommendation_ready: 'bg-purple-100 text-purple-700',
    completed: 'bg-emerald-100 text-emerald-700',
    archived: 'bg-slate-100 text-slate-500',
  };

  const statusLabels: Record<CaseStatus, string> = {
    new: 'New',
    interview_in_progress: 'Interview',
    ready_for_upload: 'Ready',
    recommendation_ready: 'Recommendation',
    completed: 'Completed',
    archived: 'Archived',
  };

  return (
    <span className={`case-status-badge ${statusStyles[status]}`}>
      {statusLabels[status]}
    </span>
  );
}

/**
 * Case card component for displaying individual cases.
 */
function CaseCard({ 
  caseSummary, 
  isSuggested = false,
  isDeleting = false,
  onClick,
  onDelete,
}: { 
  caseSummary: CaseSummary; 
  isSuggested?: boolean;
  isDeleting?: boolean;
  onClick?: (id: string) => void;
  onDelete?: (id: string) => void;
}) {
  return (
    <article 
      aria-label={
        isSuggested
          ? `Suggested case: ${caseSummary.instrumentIdentity}`
          : `Case: ${caseSummary.instrumentIdentity}`
      }
      className={`case-card ${isSuggested ? 'case-card--suggested' : ''}`}
      onClick={() => onClick?.(caseSummary.id)}
    >
      {isSuggested && (
        <span
          className="case-card__badge"
          aria-hidden="true"
        >
          Suggested
        </span>
      )}
      
      <div className="case-card__body">
        <div className={`case-card__icon ${isSuggested ? 'case-card__icon--suggested' : ''}`}>
          <Music className="case-card__icon-symbol" />
        </div>
        
        <div className="case-card__content">
          <div className="case-card__header">
            <h3 className="case-card__title">
              {getCaseDisplayName(caseSummary)}
            </h3>
            <div className="case-card__header-actions">
              <StatusBadge status={caseSummary.status} />
              {!isSuggested ? (
                <button
                  type="button"
                  className="case-card__delete-button"
                  onClick={(event) => {
                    event.stopPropagation();
                    onDelete?.(caseSummary.id);
                  }}
                  disabled={isDeleting}
                  aria-label={`Delete case ${getCaseDisplayName(caseSummary)}`}
                >
                  <Trash2 className="case-card__delete-icon" />
                  <span>{isDeleting ? 'Deleting...' : 'Delete'}</span>
                </button>
              ) : null}
            </div>
          </div>
          
          <div className="case-card__meta">
            <span className="case-card__meta-item">
              <Clock className="case-card__meta-icon" />
              {new Date(caseSummary.updatedAt).toLocaleDateString()}
            </span>
            <span>{caseSummary.scoreCount} score{caseSummary.scoreCount !== 1 ? 's' : ''}</span>
            <span>Case {getCaseShortId(caseSummary.id)}</span>
          </div>
        </div>
      </div>
    </article>
  );
}

/**
 * Main case entry page component.
 * 
 * Features:
 * - Lists existing cases from backend
 * - Highlights most recently used active case as suggested
 * - Provides "Create New Case" action
 * - Handles loading and error states
 */
export default function CaseEntryPage() {
  const router = useRouter();
  const [cases, setCases] = useState<CaseSummary[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isCreating, setIsCreating] = useState(false);
  const [deletingCaseId, setDeletingCaseId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  /**
   * Load cases from backend on mount.
   */
  const loadCases = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const fetchedCases = await casesApi.listCases();
      setCases(fetchedCases);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('Failed to load cases. Please try again.');
      }
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadCases();
  }, [loadCases]);

  /**
   * Handle creating a new case.
   */
  const handleCreateCase = useCallback(async () => {
    try {
      setIsCreating(true);
      setError(null);
      
      // Create new case via API
      const response = await casesApi.createCase({
        instrument_identity: 'placeholder', // Will be set in interview
      });
      
      // F1 ends at the dedicated new-case path, not the interview route yet.
      router.push(`/cases/new?caseId=${response.transpositionCaseId}`);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('Failed to create case. Please try again.');
      }
      setIsCreating(false);
    }
  }, [router]);

  /**
   * Handle selecting an existing case.
   */
  const handleSelectCase = useCallback((caseId: string) => {
    // Navigate to case detail or continue with existing case
    router.push(`/cases/${caseId}`);
  }, [router]);

  const handleDeleteCase = useCallback(async (caseId: string) => {
    const caseToDelete = cases.find((caseSummary) => caseSummary.id === caseId);
    if (!caseToDelete) {
      return;
    }

    try {
      setDeletingCaseId(caseId);
      setError(null);
      await casesApi.deleteCase(caseId);
      setCases((currentCases) => currentCases.filter((caseSummary) => caseSummary.id !== caseId));
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('Failed to delete case. Please try again.');
      }
    } finally {
      setDeletingCaseId(null);
    }
  }, [cases]);

  /**
   * Find the suggested case (most recently used active case).
   */
  const suggestedCase = getSuggestedCase(cases);

  const otherCases = sortCasesByUpdatedAtDesc(cases.filter(c => c.id !== suggestedCase?.id));

  return (
    <main className="case-entry-page">
      <header className="case-entry-hero">
        <p className="case-entry-hero__eyebrow">
          F1 · Case Entry
        </p>
        <h1 className="case-entry-hero__title">
          Choose a case or start a new transposition flow.
        </h1>
        <p className="case-entry-hero__description">
          Select an existing case to continue, or create a new one to start fresh.
        </p>
      </header>

      {/* Error Banner */}
      {error && (
        <div className="case-entry-error">
          <AlertCircle className="case-entry-error__icon" />
          <div className="case-entry-error__content">
            <p className="case-entry-error__text">{error}</p>
            <button
              onClick={loadCases}
              className="case-entry-error__retry"
            >
              Try again
            </button>
          </div>
        </div>
      )}

      <div className="case-entry-layout">
        {/* Suggested Case Section */}
        <section className="case-entry-section">
          <div className="case-entry-section__header">
            <h2 className="case-entry-section__title">Suggested case</h2>
          </div>
          
          {isLoading ? (
            <div className="case-entry-placeholder case-entry-placeholder--centered">
              <Loader2 className="case-entry-loader" />
            </div>
          ) : suggestedCase ? (
            <CaseCard
              caseSummary={suggestedCase}
              isSuggested
              onClick={handleSelectCase}
            />
          ) : (
            <article className="case-entry-placeholder case-entry-placeholder--empty">
              <Music className="case-entry-placeholder__icon" />
              <p className="case-entry-placeholder__title">No suggested case</p>
              <p className="case-entry-placeholder__text">Create your first case to get started</p>
            </article>
          )}
        </section>

        {/* Other Cases Section */}
        <section className="case-entry-section">
          <div className="case-entry-section__header">
            <h2 className="case-entry-section__title">Other cases</h2>
            {otherCases.length > 1 ? (
              <p className="case-entry-section__subtitle">Most recent first</p>
            ) : null}
          </div>
          <div className="case-list">
            {isLoading ? (
              <div className="case-entry-placeholder case-entry-placeholder--centered">
                <Loader2 className="case-entry-loader" />
              </div>
            ) : otherCases.length > 0 ? (
              otherCases.map((caseItem) => (
                <CaseCard
                  key={caseItem.id}
                  caseSummary={caseItem}
                  isDeleting={deletingCaseId === caseItem.id}
                  onClick={handleSelectCase}
                  onDelete={handleDeleteCase}
                />
              ))
            ) : (
              <article className="case-entry-placeholder">
                <div className="case-entry-placeholder__row">
                  <div className="case-entry-placeholder__icon-shell">
                    <Music className="case-entry-placeholder__icon-small" />
                  </div>
                  <div className="case-entry-placeholder__copy">
                    <h3 className="case-entry-placeholder__title-alt">No other cases</h3>
                    <p className="case-entry-placeholder__text">
                      {cases.length === 0 
                        ? 'Create your first case to get started' 
                        : 'All your cases are shown above'}
                    </p>
                  </div>
                </div>
              </article>
            )}
          </div>
        </section>

        {/* Create New Case Section */}
        <section className="case-entry-section">
          <h2 className="case-entry-section__title">Create new case</h2>
          <div className="new-case-action">
            <p className="new-case-action__text">
              Start a new transposition flow for a different instrument.
            </p>
            <button
              onClick={handleCreateCase}
              disabled={isCreating}
              className="new-case-action__button"
            >
              {isCreating ? (
                <>
                  <Loader2 className="new-case-action__button-icon new-case-action__button-icon--spin" />
                  <span>Creating...</span>
                </>
              ) : (
                <>
                  <PlusCircle className="new-case-action__button-icon" />
                  <span>Start New Case</span>
                </>
              )}
            </button>
          </div>
        </section>
      </div>
    </main>
  );
}
