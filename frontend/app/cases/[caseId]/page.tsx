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

function buildCaseEditDraft(caseDetail: CaseDetail) {
  return {
    instrumentIdentity: caseDetail.instrumentIdentity,
    highestPlayableTone: caseDetail.constraints.highest_playable_tone ?? '',
    lowestPlayableTone: caseDetail.constraints.lowest_playable_tone ?? '',
    restrictedTones: caseDetail.constraints.restricted_tones.join(', '),
    restrictedRegisters: caseDetail.constraints.restricted_registers.join(', '),
    difficultKeys: caseDetail.constraints.difficult_keys.join(', '),
    preferredKeys: caseDetail.constraints.preferred_keys.join(', '),
    comfortRangeMin: caseDetail.constraints.comfort_range_min ?? '',
    comfortRangeMax: caseDetail.constraints.comfort_range_max ?? '',
  };
}

function parseListInput(value: string): string[] {
  return value
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean);
}

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
  const [isEditingCase, setIsEditingCase] = useState(false);
  const [isSavingCase, setIsSavingCase] = useState(false);
  const [isResettingCase, setIsResettingCase] = useState(false);
  const [caseEditDraft, setCaseEditDraft] = useState({
    instrumentIdentity: '',
    highestPlayableTone: '',
    lowestPlayableTone: '',
    restrictedTones: '',
    restrictedRegisters: '',
    difficultKeys: '',
    preferredKeys: '',
    comfortRangeMin: '',
    comfortRangeMax: '',
  });

  useEffect(() => {
    let isMounted = true;

    async function loadCase() {
      try {
        setIsLoading(true);
        setError(null);
        const response = await casesApi.getCase(caseId);

        if (isMounted) {
          setCaseDetail(response);
          setCaseEditDraft(buildCaseEditDraft(response));
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
  const hasStaleRecommendations = recommendationResult?.recommendations.some((item) => item.isStale) ?? false;
  const recommendationFailure = recommendationResult?.failure ?? null;
  const selectedRecommendation =
    recommendationResult?.recommendations.find((item) => item.recommendationId === selectedRecommendationId) ?? null;
  const isSelectedRecommendationStale = selectedRecommendation?.isStale ?? false;
  const retryRecommendationId =
    selectedRecommendationId ?? (transformationResult?.status === 'failed' ? transformationResult.recommendationId : null);
  const canShowRecommendationAction =
    !!activeScoreDocumentId &&
    (hasStaleRecommendations || !recommendationFailure || recommendationFailure.isRetryable);
  const shouldShowRecommendationActionRow = !!activeScoreDocumentId && (isNotationPreviewReady || !!recommendationResult);

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

    async function loadRecommendations(scoreDocumentId: string) {
      if (!caseDetail) {
        return;
      }

      try {
        const response = await recommendationsApi.getRecommendations(caseDetail.id, scoreDocumentId);
        if (!isMounted) {
          return;
        }

        setRecommendationResult(response.recommendations.length || response.failure ? response : null);
      } catch (caughtError) {
        if (!isMounted) {
          return;
        }

        if (caughtError instanceof ApiError && caughtError.status === 404) {
          setRecommendationResult(null);
          return;
        }

        setRecommendationResult(null);
      }
    }

    if (!activeScoreDocumentId || !caseDetail) {
      setRecommendationResult(null);
      return;
    }

    void loadRecommendations(activeScoreDocumentId);

    return () => {
      isMounted = false;
    };
  }, [activeScoreDocumentId, caseDetail]);

  useEffect(() => {
    if (!selectedRecommendationId) {
      return;
    }

    const activeRecommendation = recommendationResult?.recommendations.find(
      (item) => item.recommendationId === selectedRecommendationId
    );

    if (!activeRecommendation || activeRecommendation.isStale) {
      setSelectedRecommendationId(null);
    }
  }, [recommendationResult, selectedRecommendationId]);

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
    if (item.isStale) {
      return;
    }
    setSelectedRecommendationId(item.recommendationId);
    setTransformationResult(null);
  }

  async function handleRunTransformation() {
    const recommendationId =
      selectedRecommendationId ?? (transformationResult?.status === 'failed' ? transformationResult.recommendationId : null);

    if (!caseDetail || !activeScoreDocumentId || !recommendationId) {
      return;
    }

    try {
      setIsTransforming(true);
      setError(null);
      const result = await transformationsApi.runTransformation(
        caseDetail.id,
        activeScoreDocumentId,
        recommendationId
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

  async function handleSaveCase() {
    if (!caseDetail) {
      return;
    }

    try {
      setIsSavingCase(true);
      setError(null);
      const updatedCase = await casesApi.updateCase(caseDetail.id, {
        instrumentIdentity: caseEditDraft.instrumentIdentity.trim(),
        constraints: {
          highest_playable_tone: caseEditDraft.highestPlayableTone.trim() || null,
          lowest_playable_tone: caseEditDraft.lowestPlayableTone.trim() || null,
          restricted_tones: parseListInput(caseEditDraft.restrictedTones),
          restricted_registers: parseListInput(caseEditDraft.restrictedRegisters),
          difficult_keys: parseListInput(caseEditDraft.difficultKeys),
          preferred_keys: parseListInput(caseEditDraft.preferredKeys),
          comfort_range_min: caseEditDraft.comfortRangeMin.trim() || null,
          comfort_range_max: caseEditDraft.comfortRangeMax.trim() || null,
        },
      });
      setCaseDetail(updatedCase);
      setCaseEditDraft(buildCaseEditDraft(updatedCase));
      setIsEditingCase(false);
      setUploadResult(null);
      setScoreResult(null);
      setPreviewError(null);
      setRecommendationResult(null);
      setSelectedRecommendationId(null);
      setTransformationResult(null);
      setTransformationError(null);
      setActivePreviewMode('original');
    } catch (caughtError) {
      if (caughtError instanceof ApiError) {
        setError(caughtError.message);
      } else {
        setError('Could not save the updated case. Please try again.');
      }
    } finally {
      setIsSavingCase(false);
    }
  }

  async function handleResetCase() {
    if (!caseDetail) {
      return;
    }

    if (typeof window !== 'undefined' && !window.confirm('Reset this case and clear its uploaded score workflow?')) {
      return;
    }

    try {
      setIsResettingCase(true);
      setError(null);
      const resetCase = await casesApi.resetCase(caseDetail.id);
      setCaseDetail(resetCase);
      setCaseEditDraft(buildCaseEditDraft(resetCase));
      setIsEditingCase(false);
      setUploadResult(null);
      setScoreResult(null);
      setPreviewError(null);
      setRecommendationResult(null);
      setSelectedRecommendationId(null);
      setTransformationResult(null);
      setTransformationError(null);
      setActivePreviewMode('original');
    } catch (caughtError) {
      if (caughtError instanceof ApiError) {
        setError(caughtError.message);
      } else {
        setError('Could not reset the case. Please try again.');
      }
    } finally {
      setIsResettingCase(false);
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
          <div className="new-case-actions new-case-actions--inline">
            <button
              type="button"
              className="new-case-actions__button new-case-actions__button--primary"
              onClick={() => setIsEditingCase((currentValue) => !currentValue)}
            >
              <span>{isEditingCase ? 'Close Edit Case' : 'Edit Case'}</span>
            </button>
            {caseDetail.status !== 'completed' ? (
              <Link href={`/interview?caseId=${caseId}&mode=edit`} className="new-case-actions__button">
                <span>Return To Interview</span>
              </Link>
            ) : null}
            <button
              type="button"
              className="new-case-actions__button"
              disabled={isResettingCase}
              onClick={() => void handleResetCase()}
            >
              <span>{isResettingCase ? 'Resetting...' : 'Reset Case'}</span>
            </button>
            <Link href="/" className="new-case-actions__button">
              <ArrowLeft className="new-case-actions__button-icon" />
              <span>Back To Cases</span>
            </Link>
          </div>
          {isEditingCase ? (
            <section className="upload-panel" aria-label="Edit case form">
              <h3 className="case-entry-section__title">Edit case constraints</h3>
              <div className="interview-range-grid">
                <label className="interview-field">
                  <span className="interview-field__label">Instrument identity</span>
                  <input
                    className="interview-field__input"
                    value={caseEditDraft.instrumentIdentity}
                    onChange={(event) =>
                      setCaseEditDraft((currentDraft) => ({
                        ...currentDraft,
                        instrumentIdentity: event.target.value,
                      }))
                    }
                  />
                </label>
                <label className="interview-field">
                  <span className="interview-field__label">Comfort range min</span>
                  <input
                    className="interview-field__input"
                    value={caseEditDraft.comfortRangeMin}
                    onChange={(event) =>
                      setCaseEditDraft((currentDraft) => ({
                        ...currentDraft,
                        comfortRangeMin: event.target.value,
                      }))
                    }
                    placeholder="e.g. G3"
                  />
                </label>
                <label className="interview-field">
                  <span className="interview-field__label">Comfort range max</span>
                  <input
                    className="interview-field__input"
                    value={caseEditDraft.comfortRangeMax}
                    onChange={(event) =>
                      setCaseEditDraft((currentDraft) => ({
                        ...currentDraft,
                        comfortRangeMax: event.target.value,
                      }))
                    }
                    placeholder="e.g. D5"
                  />
                </label>
                <label className="interview-field">
                  <span className="interview-field__label">Highest playable tone</span>
                  <input
                    className="interview-field__input"
                    value={caseEditDraft.highestPlayableTone}
                    onChange={(event) =>
                      setCaseEditDraft((currentDraft) => ({
                        ...currentDraft,
                        highestPlayableTone: event.target.value,
                      }))
                    }
                  />
                </label>
                <label className="interview-field">
                  <span className="interview-field__label">Lowest playable tone</span>
                  <input
                    className="interview-field__input"
                    value={caseEditDraft.lowestPlayableTone}
                    onChange={(event) =>
                      setCaseEditDraft((currentDraft) => ({
                        ...currentDraft,
                        lowestPlayableTone: event.target.value,
                      }))
                    }
                  />
                </label>
                <label className="interview-field">
                  <span className="interview-field__label">Restricted tones</span>
                  <input
                    className="interview-field__input"
                    value={caseEditDraft.restrictedTones}
                    onChange={(event) =>
                      setCaseEditDraft((currentDraft) => ({
                        ...currentDraft,
                        restrictedTones: event.target.value,
                      }))
                    }
                    placeholder="comma separated"
                  />
                </label>
                <label className="interview-field">
                  <span className="interview-field__label">Restricted registers</span>
                  <input
                    className="interview-field__input"
                    value={caseEditDraft.restrictedRegisters}
                    onChange={(event) =>
                      setCaseEditDraft((currentDraft) => ({
                        ...currentDraft,
                        restrictedRegisters: event.target.value,
                      }))
                    }
                    placeholder="comma separated"
                  />
                </label>
                <label className="interview-field">
                  <span className="interview-field__label">Difficult keys</span>
                  <input
                    className="interview-field__input"
                    value={caseEditDraft.difficultKeys}
                    onChange={(event) =>
                      setCaseEditDraft((currentDraft) => ({
                        ...currentDraft,
                        difficultKeys: event.target.value,
                      }))
                    }
                    placeholder="comma separated"
                  />
                </label>
                <label className="interview-field">
                  <span className="interview-field__label">Preferred keys</span>
                  <input
                    className="interview-field__input"
                    value={caseEditDraft.preferredKeys}
                    onChange={(event) =>
                      setCaseEditDraft((currentDraft) => ({
                        ...currentDraft,
                        preferredKeys: event.target.value,
                      }))
                    }
                    placeholder="comma separated"
                  />
                </label>
              </div>
              <div className="new-case-actions new-case-actions--inline">
                <button
                  type="button"
                  className="new-case-actions__button new-case-actions__button--primary"
                  disabled={isSavingCase || !caseEditDraft.instrumentIdentity.trim()}
                  onClick={() => void handleSaveCase()}
                >
                  <span>{isSavingCase ? 'Saving...' : 'Save Case Changes'}</span>
                </button>
              </div>
            </section>
          ) : null}
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
              {shouldShowRecommendationActionRow ? (
                <div className="new-case-actions new-case-actions--inline score-preview__actions">
                  {canShowRecommendationAction ? (
                    <button
                      type="button"
                      className="new-case-actions__button new-case-actions__button--primary"
                      disabled={isGeneratingRecommendations || !activeScoreDocumentId}
                      onClick={() => void handleGenerateRecommendations()}
                    >
                      <span>
                        {isGeneratingRecommendations
                          ? 'Generating...'
                          : recommendationFailure?.isRetryable
                            ? 'Retry Recommendations'
                            : 'Load Recommendations'}
                      </span>
                    </button>
                  ) : null}
                  {resultDownloadUrl ? (
                    <a
                      href={resultDownloadUrl}
                      className="new-case-actions__button"
                    >
                      <span>Download Result MusicXML</span>
                    </a>
                  ) : null}
                </div>
              ) : null}
              {recommendationResult ? (
                <section className="recommendation-workspace" aria-label="Recommendation review">
                  <div className="recommendation-workspace__header">
                    <div>
                      <p className="new-case-hero__eyebrow">F8 · Recommendation Review</p>
                      <h3 className="case-entry-section__title">Review and choose a recommendation</h3>
                    </div>
                    <Link href={`/interview?caseId=${caseId}&mode=edit`} className="new-case-actions__button">
                      <span>Return To Interview</span>
                    </Link>
                  </div>
                  {recommendationResult.status === 'blocked' && recommendationResult.failure ? (
                    <div className="case-entry-error">
                      <AlertCircle className="case-entry-error__icon" />
                      <div className="case-entry-error__content">
                        <p className="case-entry-error__text">{recommendationResult.failure.safeSummary}</p>
                        <p className="case-entry-error__text">
                          {recommendationResult.failure.isRetryable
                            ? 'Retry is available for this recommendation failure.'
                            : 'Retry is not available for this recommendation failure.'}
                        </p>
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
                        {item.isStale ? (
                          <p className="recommendation-card__meta">Stale recommendation. Regenerate recommendations before transforming.</p>
                        ) : null}
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
                          disabled={item.isStale}
                          onClick={() => handleSelectRecommendation(item)}
                        >
                          <span>
                            {item.isStale
                              ? 'Stale recommendation'
                              : selectedRecommendationId === item.recommendationId
                                ? 'Selected'
                                : 'Select recommendation'}
                          </span>
                        </button>
                      </article>
                    ))}
                  </div>
                  {hasStaleRecommendations ? (
                    <div className="interview-follow-up">
                      <div>
                        <p className="interview-follow-up__title">Recommendation refresh required</p>
                        <p className="interview-follow-up__text">
                          At least one recommendation is stale because the case constraints changed. Load recommendations again
                          before running a transformation.
                        </p>
                      </div>
                    </div>
                  ) : null}
                  {selectedRecommendationId || (transformationResult?.status === 'failed' && transformationResult.isRetryable) ? (
                    <>
                      <p className="recommendation-workspace__selection">
                        {isSelectedRecommendationStale
                          ? 'The selected recommendation is stale and cannot be used. Regenerate recommendations before continuing.'
                          : transformationResult?.status === 'failed'
                            ? transformationResult.isRetryable
                              ? 'The last transformation failed in a retryable way. You can retry it safely.'
                              : 'The last transformation failed and cannot be retried safely from the current state.'
                            : 'A recommendation is selected for the next transformation step. No automatic transformation has started.'}
                      </p>
                      <div className="new-case-actions new-case-actions--inline">
                        {retryRecommendationId && (!transformationResult || transformationResult.status !== 'failed' || transformationResult.isRetryable) ? (
                          <button
                            type="button"
                            className="new-case-actions__button new-case-actions__button--primary"
                            disabled={isTransforming || isSelectedRecommendationStale}
                            onClick={() => void handleRunTransformation()}
                          >
                            <span>
                              {isTransforming
                                ? 'Transforming...'
                                : transformationResult?.status === 'failed'
                                  ? 'Retry Transformation'
                                  : 'Run Transformation'}
                            </span>
                          </button>
                        ) : null}
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
                        {transformationResult.failureCode ? (
                          <p className="interview-follow-up__text">Failure type: {transformationResult.failureCode}</p>
                        ) : null}
                        {transformationResult.status === 'failed' ? (
                          <p className="interview-follow-up__text">
                            {transformationResult.isRetryable
                              ? 'Retry is available for this failure.'
                              : 'Retry is not available for this failure.'}
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
                        {transformationResult.failureCode ? (
                          <p className="interview-follow-up__text">Failure type: {transformationResult.failureCode}</p>
                        ) : null}
                        {transformationResult.status === 'failed' ? (
                          <p className="interview-follow-up__text">
                            {transformationResult.isRetryable
                              ? 'Retry is available for this failure.'
                              : 'Retry is not available for this failure.'}
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
