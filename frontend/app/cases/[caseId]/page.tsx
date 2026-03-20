'use client';

import { ChangeEvent, useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { AlertCircle, ArrowLeft, Clock, Loader2, Music } from 'lucide-react';

import { ScoreViewer } from '@/components/score-preview/ScoreViewer';
import { ApiError, casesApi } from '@/shared/api/cases';
import { recommendationsApi } from '@/shared/api/recommendations';
import { scoresApi } from '@/shared/api/scores';
import type { CaseDetail } from '@/shared/types/cases';
import type { RecommendationItem, RecommendationResponse } from '@/shared/types/recommendations';
import type { ScorePreviewResponse, ScoreUploadResponse } from '@/shared/types/scores';

export default function CaseDetailPage() {
  const params = useParams<{ caseId: string }>();
  const caseId = typeof params?.caseId === 'string' ? params.caseId : '';

  const [caseDetail, setCaseDetail] = useState<CaseDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<ScoreUploadResponse | null>(null);
  const [previewResult, setPreviewResult] = useState<ScorePreviewResponse | null>(null);
  const [isLoadingPreview, setIsLoadingPreview] = useState(false);
  const [recommendationResult, setRecommendationResult] = useState<RecommendationResponse | null>(null);
  const [isGeneratingRecommendations, setIsGeneratingRecommendations] = useState(false);
  const [selectedRecommendationId, setSelectedRecommendationId] = useState<string | null>(null);
  const [activePreviewMode, setActivePreviewMode] = useState<'original' | 'result'>('original');

  useEffect(() => {
    let isMounted = true;

    async function loadCase() {
      try {
        setIsLoading(true);
        setError(null);
        const response = await casesApi.getCase(caseId);

        if (isMounted) {
          setCaseDetail(response);
        }
      } catch (caughtError) {
        if (!isMounted) {
          return;
        }

        if (caughtError instanceof ApiError) {
          setError(caughtError.message);
        } else {
          setError('Could not load the selected case. Please try again.');
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    if (!caseId) {
      setError('No case identifier was provided.');
      setIsLoading(false);
      return;
    }

    void loadCase();

    return () => {
      isMounted = false;
    };
  }, [caseId]);

  const activeScoreDocumentId = uploadResult?.scoreDocumentId ?? caseDetail?.latestScoreDocumentId ?? null;

  useEffect(() => {
    let isMounted = true;

    async function loadPreview(scoreDocumentId: string) {
      try {
        setIsLoadingPreview(true);
        const response = await scoresApi.getScorePreview(scoreDocumentId);

        if (isMounted) {
          setPreviewResult(response);
        }
      } catch (caughtError) {
        if (!isMounted) {
          return;
        }

        if (caughtError instanceof ApiError) {
          setError(caughtError.message);
        } else {
          setError('Could not load the score preview. Please try again.');
        }
      } finally {
        if (isMounted) {
          setIsLoadingPreview(false);
        }
      }
    }

    if (!activeScoreDocumentId) {
      setPreviewResult(null);
      return;
    }

    void loadPreview(activeScoreDocumentId);

    return () => {
      isMounted = false;
    };
  }, [activeScoreDocumentId]);

  async function handleUpload() {
    if (!caseDetail || !selectedFile) {
      return;
    }

    try {
      setIsUploading(true);
      setError(null);
      setUploadResult(await scoresApi.uploadScore(caseDetail.id, selectedFile));
      const refreshedCase = await casesApi.getCase(caseDetail.id);
      setCaseDetail(refreshedCase);
      setPreviewResult(null);
      setRecommendationResult(null);
      setSelectedRecommendationId(null);
      setSelectedFile(null);
      setActivePreviewMode('original');
    } catch (caughtError) {
      if (caughtError instanceof ApiError) {
        setError(caughtError.message);
      } else {
        setError('Could not upload the selected score. Please try again.');
      }
    } finally {
      setIsUploading(false);
    }
  }

  async function handleGenerateRecommendations() {
    if (!caseDetail || !uploadResult) {
      return;
    }

    try {
      setIsGeneratingRecommendations(true);
      setError(null);
      const result = await recommendationsApi.generateRecommendations(caseDetail.id, uploadResult.scoreDocumentId);
      setRecommendationResult(result);
      setSelectedRecommendationId(null);
    } catch (caughtError) {
      if (caughtError instanceof ApiError) {
        setError(caughtError.message);
      } else {
        setError('Could not generate recommendations. Please try again.');
      }
    } finally {
      setIsGeneratingRecommendations(false);
    }
  }

  function handleSelectRecommendation(item: RecommendationItem) {
    setSelectedRecommendationId(item.recommendationId);
  }

  return (
    <main className="new-case-page">
      <header className="new-case-hero">
        <p className="new-case-hero__eyebrow">F1 · Existing Case</p>
        <h1 className="new-case-hero__title">Continue an existing case.</h1>
        <p className="new-case-hero__description">
          This screen confirms that an existing case can be reopened from the case entry page without hitting a 404.
        </p>
      </header>

      {isLoading ? (
        <section className="case-entry-section">
          <div className="case-entry-placeholder case-entry-placeholder--centered">
            <Loader2 className="case-entry-loader" />
          </div>
        </section>
      ) : error ? (
        <section className="case-entry-error">
          <AlertCircle className="case-entry-error__icon" />
          <div className="case-entry-error__content">
            <p className="case-entry-error__text">{error}</p>
          </div>
        </section>
      ) : caseDetail ? (
        <section className="case-entry-section">
          <h2 className="case-entry-section__title">Case overview</h2>
          <article className="case-card case-card--suggested" aria-label={`Existing case: ${caseDetail.instrumentIdentity}`}>
            <span className="case-card__badge">Active case</span>
            <div className="case-card__body">
              <div className="case-card__icon case-card__icon--suggested">
                <Music className="case-card__icon-symbol" />
              </div>
              <div className="case-card__content">
                <div className="case-card__header">
                  <h3 className="case-card__title">{caseDetail.instrumentIdentity}</h3>
                </div>
                <div className="case-card__meta">
                  <span className="case-card__meta-item">
                    <Clock className="case-card__meta-icon" />
                    {new Date(caseDetail.updatedAt).toLocaleDateString()}
                  </span>
                  <span>{caseDetail.scoreCount} score{caseDetail.scoreCount !== 1 ? 's' : ''}</span>
                  <span>Status: {caseDetail.status}</span>
                </div>
              </div>
            </div>
          </article>
          {(caseDetail.status === 'new' || caseDetail.status === 'interview_in_progress') ? (
            <div className="new-case-actions new-case-actions--inline">
              <Link
                href={`/interview?caseId=${caseId}`}
                className="new-case-actions__button new-case-actions__button--primary"
              >
                <span>{caseDetail.status === 'new' ? 'Begin Interview' : 'Continue Interview'}</span>
              </Link>
            </div>
          ) : null}
          {caseDetail.status === 'ready_for_upload' ? (
            <div className="upload-panel">
              <h3 className="case-entry-section__title">Upload original score</h3>
              <p className="case-card__text">
                Upload a MusicXML file to start the score-processing flow for this case.
              </p>
              <label className="interview-field">
                <span className="interview-field__label">MusicXML file</span>
                <input
                  className="interview-field__input"
                  type="file"
                  accept=".musicxml,.xml,.mxl,text/xml,application/xml,application/vnd.recordare.musicxml"
                  onChange={(event: ChangeEvent<HTMLInputElement>) =>
                    setSelectedFile(event.target.files?.[0] ?? null)
                  }
                />
              </label>
              <div className="new-case-actions new-case-actions--inline">
                <button
                  type="button"
                  className="new-case-actions__button new-case-actions__button--primary"
                  disabled={isUploading || selectedFile === null}
                  onClick={() => void handleUpload()}
                >
                  <span>{isUploading ? 'Uploading...' : 'Upload MusicXML'}</span>
                </button>
              </div>
              {uploadResult?.acceptedStatus === 'parse_failed' ? (
                <div className="interview-follow-up">
                  <div>
                    <p className="interview-follow-up__title">Score parsing failed</p>
                    <p className="interview-follow-up__text">{uploadResult.originalFilename} could not be parsed safely.</p>
                    {uploadResult.initialProcessingSnapshot.parseFailureType ? (
                      <p className="interview-follow-up__text">
                        Failure type: {uploadResult.initialProcessingSnapshot.parseFailureType}
                      </p>
                    ) : null}
                  </div>
                </div>
              ) : null}
              {activeScoreDocumentId ? (
                <section className="score-preview" aria-label="Score preview workspace">
                  <div className="score-preview__header">
                    <div>
                      <p className="new-case-hero__eyebrow">F8b · Score Preview</p>
                      <h3 className="case-entry-section__title">Inspect the uploaded score safely</h3>
                    </div>
                    <div className="score-preview__tabs" role="tablist" aria-label="Preview mode">
                      <button
                        type="button"
                        role="tab"
                        aria-selected={activePreviewMode === 'original'}
                        className={`score-preview__tab ${activePreviewMode === 'original' ? 'score-preview__tab--active' : ''}`}
                        onClick={() => setActivePreviewMode('original')}
                      >
                        Original
                      </button>
                      <button
                        type="button"
                        role="tab"
                        aria-selected={activePreviewMode === 'result'}
                        className="score-preview__tab score-preview__tab--disabled"
                        disabled
                      >
                        Result
                      </button>
                    </div>
                  </div>
                  <div className="score-preview__panel" aria-live="polite">
                    {isLoadingPreview ? (
                      <div className="score-preview__state">
                        <Loader2 className="case-entry-loader" />
                        <p className="score-preview__summary">Loading the read-only preview.</p>
                      </div>
                    ) : previewResult ? (
                      <>
                        {previewResult.availability !== 'ready' ? (
                          <div className="score-preview__status">
                            <span className={`score-preview__availability score-preview__availability--${previewResult.availability}`}>
                              {previewResult.availability}
                            </span>
                            <p className="score-preview__summary">{previewResult.safeSummary}</p>
                          </div>
                        ) : null}
                        <div className="score-preview__surface" aria-label="Read-only score preview">
                          <p className="score-preview__surface-label">Read-only preview</p>
                          <h4 className="score-preview__surface-title">
                            {previewResult.canonicalScoreSummary?.title || previewResult.originalFilename || 'Uploaded score'}
                          </h4>
                          <p className="score-preview__surface-meta">
                            {previewResult.rendererFormat || 'preview'}{previewResult.pageCount ? ` · ${previewResult.pageCount} page(s)` : ''}
                          </p>
                          {previewResult.availability === 'ready' && previewResult.previewAccess ? (
                            <ScoreViewer
                              previewAccess={previewResult.previewAccess}
                              title={previewResult.canonicalScoreSummary?.title || previewResult.originalFilename || 'Uploaded score'}
                            />
                          ) : null}
                          {previewResult.failureCode ? (
                            <p className="score-preview__failure">Failure type: {previewResult.failureCode}</p>
                          ) : null}
                        </div>
                        <p className="score-preview__note">
                          Preview stays read-only. Result comparison becomes available after a later result artifact exists.
                        </p>
                      </>
                    ) : (
                      <div className="score-preview__state">
                        <p className="score-preview__summary">No preview is available yet.</p>
                      </div>
                    )}
                  </div>
                </section>
              ) : null}
              {uploadResult?.acceptedStatus === 'parsed' ? (
                <div className="new-case-actions new-case-actions--inline">
                  <button
                    type="button"
                    className="new-case-actions__button new-case-actions__button--primary"
                    disabled={isGeneratingRecommendations}
                    onClick={() => void handleGenerateRecommendations()}
                  >
                    <span>{isGeneratingRecommendations ? 'Generating...' : 'Load Recommendations'}</span>
                  </button>
                </div>
              ) : null}
              {recommendationResult ? (
                <section className="recommendation-workspace" aria-label="Recommendation review">
                  <div className="recommendation-workspace__header">
                    <div>
                      <p className="new-case-hero__eyebrow">F8 · Recommendation Review</p>
                      <h3 className="case-entry-section__title">Review and choose a recommendation</h3>
                    </div>
                  </div>
                  {recommendationResult.status === 'blocked' && recommendationResult.failure ? (
                    <div className="case-entry-error">
                      <AlertCircle className="case-entry-error__icon" />
                      <div className="case-entry-error__content">
                        <p className="case-entry-error__text">{recommendationResult.failure.safeSummary}</p>
                      </div>
                    </div>
                  ) : null}
                  <div className="recommendation-grid">
                    {recommendationResult.recommendations.map((item) => (
                      <article
                        key={item.recommendationId}
                        className={`recommendation-card ${item.isPrimary ? 'recommendation-card--primary' : 'recommendation-card--secondary'} ${
                          selectedRecommendationId === item.recommendationId ? 'recommendation-card--selected' : ''
                        }`}
                      >
                        <div className="recommendation-card__header">
                          <div>
                            <p className="recommendation-card__eyebrow">
                              {item.isPrimary ? 'Primary option' : 'Secondary option'}
                            </p>
                            <h4 className="recommendation-card__title">{item.label}</h4>
                          </div>
                          <span className={`recommendation-card__confidence recommendation-card__confidence--${item.confidence}`}>
                            {item.confidence}
                          </span>
                        </div>
                        <p className="recommendation-card__range">
                          {item.targetRange.min} to {item.targetRange.max}
                        </p>
                        <p className="recommendation-card__reason">{item.summaryReason}</p>
                        {item.recommendedKey ? (
                          <p className="recommendation-card__meta">Recommended key: {item.recommendedKey}</p>
                        ) : null}
                        {item.warnings.length ? (
                          <ul className="recommendation-card__warnings">
                            {item.warnings.map((warning) => (
                              <li
                                key={`${item.recommendationId}-${warning.code}`}
                                className={`recommendation-card__warning recommendation-card__warning--${warning.severity}`}
                              >
                                {warning.message}
                              </li>
                            ))}
                          </ul>
                        ) : null}
                        <button
                          type="button"
                          className="new-case-actions__button"
                          onClick={() => handleSelectRecommendation(item)}
                        >
                          <span>{selectedRecommendationId === item.recommendationId ? 'Selected' : 'Select recommendation'}</span>
                        </button>
                      </article>
                    ))}
                  </div>
                  {selectedRecommendationId ? (
                    <p className="recommendation-workspace__selection">
                      A recommendation is selected for the next transformation step. No automatic transformation has started.
                    </p>
                  ) : null}
                </section>
              ) : null}
            </div>
          ) : null}
        </section>
      ) : null}

      <div className="new-case-actions">
        <Link href="/" className="new-case-actions__button">
          <ArrowLeft className="new-case-actions__button-icon" />
          <span>Back To Cases</span>
        </Link>
      </div>
    </main>
  );
}
