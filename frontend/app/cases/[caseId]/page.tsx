'use client';

import { ChangeEvent, useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { AlertCircle, ArrowLeft, Clock, Loader2, Music } from 'lucide-react';

import { ApiError, casesApi } from '@/shared/api/cases';
import { scoresApi } from '@/shared/api/scores';
import type { CaseDetail } from '@/shared/types/cases';
import type { ScoreUploadResponse } from '@/shared/types/scores';

export default function CaseDetailPage() {
  const params = useParams<{ caseId: string }>();
  const caseId = typeof params?.caseId === 'string' ? params.caseId : '';

  const [caseDetail, setCaseDetail] = useState<CaseDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<ScoreUploadResponse | null>(null);

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
      setSelectedFile(null);
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
                  accept=".musicxml,.xml,text/xml,application/xml"
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
              {uploadResult ? (
                <div className="interview-follow-up">
                  <div>
                    <p className="interview-follow-up__title">Upload accepted</p>
                    <p className="interview-follow-up__text">
                      {uploadResult.originalFilename} was accepted with status {uploadResult.acceptedStatus}.
                    </p>
                  </div>
                </div>
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
