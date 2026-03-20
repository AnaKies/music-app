'use client';

import { ChangeEvent, useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { AlertCircle, ArrowLeft, Clock, Loader2, Music } from 'lucide-react';

import { ScoreViewer } from '@/components/score-preview/ScoreViewer';
import { ApiError, casesApi } from '@/shared/api/cases';
import { recommendationsApi } from '@/shared/api/recommendations';
import { scoresApi } from '@/shared/api/scores';
import { transformationsApi } from '@/shared/api/transformations';
import type { CaseDetail } from '@/shared/types/cases';
import type { RecommendationItem, RecommendationResponse } from '@/shared/types/recommendations';
import type { ScorePreviewResponse, ScoreReadResponse, ScoreUploadResponse } from '@/shared/types/scores';
import type { TransformationResponse } from '@/shared/types/transformations';

export default function CaseDetailPage() {
  const params = useParams<{ caseId: string }>();
  const caseId = typeof params?.caseId === 'string' ? params.caseId : '';

  const [caseDetail, setCaseDetail] = useState<CaseDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<ScoreUploadResponse | null>(null);
  const [scoreResult, setScoreResult] = useState<ScoreReadResponse | null>(null);
  const [previewError, setPreviewError] = useState<string | null>(null);
  const [isLoadingScore, setIsLoadingScore] = useState(false);
  const [recommendationResult, setRecommendationResult] = useState<RecommendationResponse | null>(null);
  const [isGeneratingRecommendations, setIsGeneratingRecommendations] = useState(false);
  const [selectedRecommendationId, setSelectedRecommendationId] = useState<string | null>(null);
  const [transformationResult, setTransformationResult] = useState<TransformationResponse | null>(null);
  const [isTransforming, setIsTransforming] = useState(false);
  const [isLoadingTransformation, setIsLoadingTransformation] = useState(false);
  const [transformationError, setTransformationError] = useState<string | null>(null);
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
  const sourcePreviewResult: ScorePreviewResponse | null = scoreResult?.sourcePreview ?? null;
  const resultPreviewResult: ScorePreviewResponse | null = scoreResult?.resultPreview ?? null;
  const previewResult: ScorePreviewResponse | null =
    activePreviewMode === 'result' ? resultPreviewResult : sourcePreviewResult;
  const isNotationPreviewReady = sourcePreviewResult?.availability === 'ready';
  const isResultPreviewReady = resultPreviewResult?.availability === 'ready';
  const resultDownloadUrl =
    activeScoreDocumentId && isResultPreviewReady ? scoresApi.getResultDownloadUrl(activeScoreDocumentId) : null;

  useEffect(() => {
    let isMounted = true;

    async function loadScore(scoreDocumentId: string) {
      try {
        setIsLoadingScore(true);
        setPreviewError(null);
        const response = await scoresApi.getScore(scoreDocumentId);

        if (isMounted) {
          setScoreResult(response);
        }
      } catch (caughtError) {
        if (!isMounted) {
          return;
        }

        if (caughtError instanceof ApiError) {
          setPreviewError(caughtError.message);
        } else {
          setPreviewError('Could not load the score preview. Please try again.');
        }
      } finally {
        if (isMounted) {
          setIsLoadingScore(false);
        }
      }
    }

    if (!activeScoreDocumentId) {
      setScoreResult(null);
      setPreviewError(null);
      return;
    }

    void loadScore(activeScoreDocumentId);

    return () => {
      isMounted = false;
    };
  }, [activeScoreDocumentId]);

  useEffect(() => {
    let isMounted = true;

    async function loadTransformation(transformationJobId: string) {
      try {
        setIsLoadingTransformation(true);
        setTransformationError(null);
        const response = await transformationsApi.getTransformation(transformationJobId);
        if (isMounted) {
          setTransformationResult(response);
        }
      } catch (caughtError) {
        if (!isMounted) {
          return;
        }

        if (caughtError instanceof ApiError) {
          setTransformationError(caughtError.message);
        } else {
          setTransformationError('Could not load the transformation status. Please try again.');
        }
      } finally {
        if (isMounted) {
          setIsLoadingTransformation(false);
        }
      }
    }

    if (!scoreResult?.latestTransformationJobId) {
      if (!isTransforming) {
        setTransformationResult(null);
      }
      setTransformationError(null);
      return;
    }

    void loadTransformation(scoreResult.latestTransformationJobId);

    return () => {
      isMounted = false;
    };
  }, [scoreResult?.latestTransformationJobId, isTransforming]);

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
      setScoreResult(null);
      setPreviewError(null);
      setRecommendationResult(null);
      setSelectedRecommendationId(null);
      setTransformationResult(null);
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
    if (!caseDetail || !activeScoreDocumentId) {
      return;
    }

    try {
      setIsGeneratingRecommendations(true);
      setError(null);
      const result = await recommendationsApi.generateRecommendations(caseDetail.id, activeScoreDocumentId);
      setRecommendationResult(result);
      setSelectedRecommendationId(null);
      setTransformationResult(null);
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
    setTransformationResult(null);
  }

  async function handleRunTransformation() {
    if (!caseDetail || !activeScoreDocumentId || !selectedRecommendationId) {
      return;
    }

    try {
      setIsTransforming(true);
      setError(null);
      const result = await transformationsApi.runTransformation(
        caseDetail.id,
        activeScoreDocumentId,
        selectedRecommendationId
      );
      const refreshedScore = await scoresApi.getScore(activeScoreDocumentId);
      setScoreResult(refreshedScore);
      setTransformationResult(result);
      setActivePreviewMode('result');
    } catch (caughtError) {
      if (caughtError instanceof ApiError) {
        setError(caughtError.message);
      } else {
        setError('Could not run the deterministic transformation. Please try again.');
      }
    } finally {
      setIsTransforming(false);
    }
  }

  return (
    <main className="new-case-page">
      <header className="new-case-hero">
        <p className="new-case-hero__eyebrow">F1 · Existing Case</p>
        <h1 className="new-case-hero__title">Continue an existing case.</h1>
        <p className="new-case-hero__description">Review the current case, upload a score, and continue the transposition flow.</p>
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
              {uploadResult?.acceptedStatus !== 'parsed' ? (
                <div className="new-case-actions new-case-actions--inline score-preview__actions">
                  <button
                    type="button"
                    className="new-case-actions__button new-case-actions__button--primary"
                    disabled={isUploading || selectedFile === null}
                    onClick={() => void handleUpload()}
                  >
                    <span>{isUploading ? 'Uploading...' : 'Upload MusicXML'}</span>
                  </button>
                  <Link href="/" className="new-case-actions__button">
                    <ArrowLeft className="new-case-actions__button-icon" />
                    <span>Back To Cases</span>
                  </Link>
                </div>
              ) : null}
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
              {isNotationPreviewReady ? (
                <div className="new-case-actions new-case-actions--inline score-preview__actions">
                  <button
                    type="button"
                    className="new-case-actions__button new-case-actions__button--primary"
                    disabled={isGeneratingRecommendations}
                    onClick={() => void handleGenerateRecommendations()}
                  >
                    <span>{isGeneratingRecommendations ? 'Generating...' : 'Load Recommendations'}</span>
                  </button>
                  {resultDownloadUrl ? (
                    <a
                      href={resultDownloadUrl}
                      className="new-case-actions__button"
                    >
                      <span>Download Result MusicXML</span>
                    </a>
                  ) : null}
                  <Link href="/" className="new-case-actions__button">
                    <ArrowLeft className="new-case-actions__button-icon" />
                    <span>Back To Cases</span>
                  </Link>
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
                    <>
                      <p className="recommendation-workspace__selection">
                        A recommendation is selected for the next transformation step. No automatic transformation has started.
                      </p>
                      <div className="new-case-actions new-case-actions--inline">
                        <button
                          type="button"
                          className="new-case-actions__button new-case-actions__button--primary"
                          disabled={isTransforming}
                          onClick={() => void handleRunTransformation()}
                        >
                          <span>{isTransforming ? 'Transforming...' : 'Run Transformation'}</span>
                        </button>
                      </div>
                    </>
                  ) : null}
                  {transformationResult ? (
                    <div className="interview-follow-up">
                      <div>
                        <p className="interview-follow-up__title">Deterministic transformation</p>
                        <p className="interview-follow-up__text">{transformationResult.safeSummary}</p>
                        <p className="interview-follow-up__text">
                          Applied range: {transformationResult.selectedRangeMin} to {transformationResult.selectedRangeMax}
                        </p>
                        {transformationResult.semitoneShift !== null && transformationResult.semitoneShift !== undefined ? (
                          <p className="interview-follow-up__text">
                            Semitone shift: {transformationResult.semitoneShift}
                          </p>
                        ) : null}
                        {transformationResult.warnings.length ? (
                          <ul className="recommendation-card__warnings">
                            {transformationResult.warnings.map((warning) => (
                              <li
                                key={`${transformationResult.transformationJobId}-${warning.code}`}
                                className={`recommendation-card__warning recommendation-card__warning--${warning.severity}`}
                              >
                                {warning.message}
                              </li>
                            ))}
                          </ul>
                        ) : null}
                      </div>
                    </div>
                  ) : isLoadingTransformation ? (
                    <div className="interview-follow-up">
                      <div>
                        <p className="interview-follow-up__title">Deterministic transformation</p>
                        <p className="interview-follow-up__text">Loading the latest transformation status.</p>
                      </div>
                    </div>
                  ) : transformationError ? (
                    <div className="interview-follow-up">
                      <div>
                        <p className="interview-follow-up__title">Deterministic transformation</p>
                        <p className="interview-follow-up__text">{transformationError}</p>
                      </div>
                    </div>
                  ) : null}
                </section>
              ) : null}
              {!recommendationResult && (transformationResult || isLoadingTransformation || transformationError) ? (
                <section className="recommendation-workspace" aria-label="Transformation status">
                  {transformationResult ? (
                    <div className="interview-follow-up">
                      <div>
                        <p className="interview-follow-up__title">Deterministic transformation</p>
                        <p className="interview-follow-up__text">{transformationResult.safeSummary}</p>
                        <p className="interview-follow-up__text">
                          Applied range: {transformationResult.selectedRangeMin} to {transformationResult.selectedRangeMax}
                        </p>
                        {transformationResult.semitoneShift !== null && transformationResult.semitoneShift !== undefined ? (
                          <p className="interview-follow-up__text">
                            Semitone shift: {transformationResult.semitoneShift}
                          </p>
                        ) : null}
                        {transformationResult.warnings.length ? (
                          <ul className="recommendation-card__warnings">
                            {transformationResult.warnings.map((warning) => (
                              <li
                                key={`${transformationResult.transformationJobId}-${warning.code}`}
                                className={`recommendation-card__warning recommendation-card__warning--${warning.severity}`}
                              >
                                {warning.message}
                              </li>
                            ))}
                          </ul>
                        ) : null}
                      </div>
                    </div>
                  ) : (
                    <div className="interview-follow-up">
                      <div>
                        <p className="interview-follow-up__title">Deterministic transformation</p>
                        <p className="interview-follow-up__text">
                          {transformationError || 'Loading the latest transformation status.'}
                        </p>
                      </div>
                    </div>
                  )}
                </section>
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
                        className={`score-preview__tab ${activePreviewMode === 'result' ? 'score-preview__tab--active' : ''} ${
                          !isResultPreviewReady ? 'score-preview__tab--disabled' : ''
                        }`}
                        disabled={!isResultPreviewReady}
                        onClick={() => setActivePreviewMode('result')}
                      >
                        Result
                      </button>
                    </div>
                  </div>
                  <div className="score-preview__panel" aria-live="polite">
                    {isLoadingScore ? (
                      <div className="score-preview__state">
                        <Loader2 className="case-entry-loader" />
                        <p className="score-preview__summary">Loading the read-only preview.</p>
                      </div>
                    ) : previewError ? (
                      <div className="score-preview__state">
                        <p className="score-preview__summary">{previewError}</p>
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
                          Preview stays read-only. Result comparison becomes available once a transformed result artifact exists.
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
            </div>
          ) : null}
        </section>
      ) : null}

      {caseDetail?.status !== 'ready_for_upload' ? (
        <div className="new-case-actions">
          <Link href="/" className="new-case-actions__button">
            <ArrowLeft className="new-case-actions__button-icon" />
            <span>Back To Cases</span>
          </Link>
        </div>
      ) : null}
    </main>
  );
}
