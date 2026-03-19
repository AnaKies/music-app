'use client';

import Link from 'next/link';
import { useCallback, useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import {
  AlertCircle,
  ArrowLeft,
  CheckCircle2,
  ChevronRight,
  Loader2,
} from 'lucide-react';

import { ApiError } from '@/shared/api/cases';
import { interviewsApi } from '@/shared/api/interviews';
import type {
  InterviewAdvanceResponse,
  InterviewAnswerValue,
  InterviewDetailResponse,
  InterviewQuestion,
  InterviewQuestionOption,
  InterviewRecordedAnswer,
} from '@/shared/types/interviews';

function buildEmptyDraft() {
  return {
    selectedOption: '',
    selectedOptions: [] as string[],
    rangeMin: '',
    rangeMax: '',
    text: '',
  };
}

function buildAnswerValue(
  question: InterviewQuestion,
  draft: ReturnType<typeof buildEmptyDraft>
): InterviewAnswerValue {
  if (question.type === 'single_select') {
    return { selectedOption: draft.selectedOption };
  }

  if (question.type === 'multi_select') {
    return { selectedOptions: draft.selectedOptions };
  }

  if (question.type === 'note_range') {
    return {
      noteRange: {
        min: draft.rangeMin,
        max: draft.rangeMax,
      },
    };
  }

  return {
    text: draft.text,
  };
}

function getValidationMessage(
  question: InterviewQuestion | null,
  draft: ReturnType<typeof buildEmptyDraft>
): string | null {
  if (!question) {
    return null;
  }

  if (question.type === 'single_select' && !draft.selectedOption) {
    return 'Select one option before continuing.';
  }

  if (
    question.type === 'note_range' &&
    (!draft.rangeMin.trim() || !draft.rangeMax.trim())
  ) {
    return 'Enter both range boundaries before continuing.';
  }

  if (question.type === 'note_text' && question.required && !draft.text.trim()) {
    return 'Add the missing clarification before continuing.';
  }

  return null;
}

type InterviewViewState = InterviewAdvanceResponse & {
  collectedAnswers?: InterviewRecordedAnswer[];
};

function QuestionOptionButton({
  option,
  checked,
  onClick,
  multi = false,
}: {
  option: InterviewQuestionOption;
  checked: boolean;
  onClick: () => void;
  multi?: boolean;
}) {
  const marker = multi ? (checked ? '☑' : '☐') : checked ? '◉' : '○';

  return (
    <button
      type="button"
      className={`interview-option ${checked ? 'interview-option--selected' : ''}`}
      onClick={onClick}
      aria-pressed={checked}
      aria-label={option.label}
    >
      <span className="interview-option__marker">{marker}</span>
      <span>
        <span className="interview-option__label">{option.label}</span>
        {option.description ? (
          <span className="interview-option__description">{option.description}</span>
        ) : null}
      </span>
    </button>
  );
}

export default function InterviewPage() {
  const { replace } = useRouter();
  const searchParams = useSearchParams();
  const caseId = searchParams.get('caseId') ?? '';
  const interviewId = searchParams.get('interviewId') ?? '';

  const [responseState, setResponseState] = useState<InterviewViewState | null>(null);
  const [draft, setDraft] = useState(buildEmptyDraft());
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const currentQuestion = responseState?.nextQuestion ?? null;

  const syncResponse = useCallback(
    (response: InterviewViewState) => {
      setResponseState(response);
      setDraft(buildEmptyDraft());

      if (response.interviewId && response.interviewId !== interviewId) {
        replace(`/interview?caseId=${response.caseId}&interviewId=${response.interviewId}`);
      }
    },
    [interviewId, replace]
  );

  const loadInterview = useCallback(async () => {
    if (!caseId) {
      setError('No case identifier was provided for the interview.');
      setIsLoading(false);
      return;
    }

    try {
      setIsLoading(true);
      setError(null);

      if (interviewId) {
        const detail = await interviewsApi.getInterview(interviewId);
        syncResponse({
          interviewId: detail.interviewId,
          caseId: detail.caseId,
          status: detail.status,
          nextQuestion: detail.currentQuestion,
          progress: detail.progress,
          lowConfidence: detail.lowConfidence,
          derivedCaseSummary: detail.derivedCaseSummary,
          collectedAnswers: detail.collectedAnswers,
        });
      } else {
        syncResponse(await interviewsApi.startOrContinueInterview({ caseId }));
      }
    } catch (caughtError) {
      if (caughtError instanceof ApiError) {
        setError(caughtError.message);
      } else {
        setError('Could not load the interview session. Please try again.');
      }
    } finally {
      setIsLoading(false);
    }
  }, [caseId, interviewId, syncResponse]);

  useEffect(() => {
    void loadInterview();
  }, [loadInterview]);

  const submitCurrentQuestion = useCallback(async () => {
    if (!currentQuestion || !responseState) {
      return;
    }

    if (getValidationMessage(currentQuestion, draft) !== null) {
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);

      syncResponse(
        await interviewsApi.startOrContinueInterview({
          caseId: responseState.caseId,
          interviewId: responseState.interviewId,
          questionId: currentQuestion.id,
          answer: buildAnswerValue(currentQuestion, draft),
        })
      );
    } catch (caughtError) {
      if (caughtError instanceof ApiError) {
        setError(caughtError.message);
      } else {
        setError('Could not submit the interview answer. Please try again.');
      }
    } finally {
      setIsSubmitting(false);
    }
  }, [currentQuestion, draft, responseState, syncResponse]);

  const validationMessage = getValidationMessage(currentQuestion, draft);

  return (
    <main className="interview-page">
      <header className="interview-hero">
        <p className="interview-hero__eyebrow">F2 · Structured Interview</p>
        <h1 className="interview-hero__title">Collect the instrument and playability constraints step by step.</h1>
        <p className="interview-hero__description">
          The interview stays structured so later recommendation logic can separate confirmed constraints from uncertain hints.
        </p>
      </header>

      {error ? (
        <section className="case-entry-error">
          <AlertCircle className="case-entry-error__icon" />
          <div className="case-entry-error__content">
            <p className="case-entry-error__text">{error}</p>
            <button type="button" className="case-entry-error__retry" onClick={() => void loadInterview()}>
              Try again
            </button>
          </div>
        </section>
      ) : null}

      <div className="interview-layout">
        <section className="case-entry-section">
          <div className="interview-progress">
            <div>
              <p className="interview-progress__label">Progress</p>
              <h2 className="case-entry-section__title">
                Step {responseState?.progress.currentStep ?? 1} of {responseState?.progress.totalSteps ?? 4}
              </h2>
            </div>
            <div className="interview-progress__meter" aria-label="Interview progress">
              <span
                className="interview-progress__meter-bar"
                style={{ width: `${responseState?.progress.percentComplete ?? 0}%` }}
              />
            </div>
          </div>

          {isLoading ? (
            <div className="case-entry-placeholder case-entry-placeholder--centered">
              <Loader2 className="case-entry-loader" />
            </div>
          ) : currentQuestion ? (
            <div className="interview-question">
              <div className="interview-question__header">
                <p className="interview-question__label">Current question</p>
                <h2 className="interview-question__title">{currentQuestion.prompt}</h2>
                {currentQuestion.helpText ? (
                  <p className="interview-question__help">{currentQuestion.helpText}</p>
                ) : null}
              </div>

              {responseState?.lowConfidence ? (
                <div className="interview-follow-up">
                  <AlertCircle className="interview-follow-up__icon" />
                  <div>
                    <p className="interview-follow-up__title">Clarification required</p>
                    <p className="interview-follow-up__text">
                      The previous answer sounded uncertain. This follow-up keeps the case structured instead of guessing.
                    </p>
                  </div>
                </div>
              ) : null}

              {currentQuestion.type === 'single_select' ? (
                <div className="interview-option-list">
                  {currentQuestion.options.map((option) => (
                    <QuestionOptionButton
                      key={option.value}
                      option={option}
                      checked={draft.selectedOption === option.value}
                      onClick={() => setDraft((currentDraft) => ({ ...currentDraft, selectedOption: option.value }))}
                    />
                  ))}
                </div>
              ) : null}

              {currentQuestion.type === 'multi_select' ? (
                <div className="interview-option-list">
                  {currentQuestion.options.map((option) => {
                    const checked = draft.selectedOptions.includes(option.value);

                    return (
                      <QuestionOptionButton
                        key={option.value}
                        option={option}
                        checked={checked}
                        multi
                        onClick={() =>
                          setDraft((currentDraft) => ({
                            ...currentDraft,
                            selectedOptions: checked
                              ? currentDraft.selectedOptions.filter((value) => value !== option.value)
                              : [...currentDraft.selectedOptions, option.value],
                          }))
                        }
                      />
                    );
                  })}
                </div>
              ) : null}

              {currentQuestion.type === 'note_range' ? (
                <div className="interview-range-grid">
                  <label className="interview-field">
                    <span className="interview-field__label">Lowest comfortable note</span>
                    <input
                      className="interview-field__input"
                      value={draft.rangeMin}
                      onChange={(event) =>
                        setDraft((currentDraft) => ({ ...currentDraft, rangeMin: event.target.value }))
                      }
                      placeholder="e.g. G3"
                    />
                  </label>
                  <label className="interview-field">
                    <span className="interview-field__label">Highest comfortable note</span>
                    <input
                      className="interview-field__input"
                      value={draft.rangeMax}
                      onChange={(event) =>
                        setDraft((currentDraft) => ({ ...currentDraft, rangeMax: event.target.value }))
                      }
                      placeholder="e.g. D5"
                    />
                  </label>
                </div>
              ) : null}

              {currentQuestion.type === 'note_text' ? (
                <label className="interview-field">
                  <span className="interview-field__label">Interview note</span>
                  <textarea
                    className="interview-field__textarea"
                    value={draft.text}
                    onChange={(event) => setDraft((currentDraft) => ({ ...currentDraft, text: event.target.value }))}
                    placeholder={currentQuestion.placeholder ?? 'Add your note'}
                  />
                </label>
              ) : null}

              <div className="interview-actions">
                {validationMessage ? (
                  <p className="interview-actions__validation">{validationMessage}</p>
                ) : null}
                <button
                  type="button"
                  className="interview-actions__submit"
                  onClick={() => void submitCurrentQuestion()}
                  disabled={isSubmitting || validationMessage !== null}
                >
                  {isSubmitting ? <Loader2 className="case-entry-loader" /> : <ChevronRight className="new-case-actions__button-icon" />}
                  <span>{isSubmitting ? 'Submitting...' : 'Submit answer'}</span>
                </button>
              </div>
            </div>
          ) : (
            <div className="interview-complete">
              <CheckCircle2 className="interview-complete__icon" />
              <div>
                <h2 className="interview-complete__title">Interview session complete</h2>
                <p className="interview-complete__text">
                  The interview has collected enough structured constraints for the next backend persistence step.
                </p>
              </div>
            </div>
          )}
        </section>

        <aside className="case-entry-section">
          <p className="interview-progress__label">Derived case summary</p>
          <div className="interview-summary">
            <div>
              <span className="interview-summary__term">Instrument</span>
              <strong className="interview-summary__value">{responseState?.derivedCaseSummary.instrumentIdentity ?? 'Pending'}</strong>
            </div>
            <div>
              <span className="interview-summary__term">Confirmed constraints</span>
              <strong className="interview-summary__value">
                {responseState?.derivedCaseSummary.confirmedConstraintCount ?? 0}
              </strong>
            </div>
            <div>
              <span className="interview-summary__term">Comfort range</span>
              <strong className="interview-summary__value">
                {responseState?.derivedCaseSummary.comfortRangeMin && responseState?.derivedCaseSummary.comfortRangeMax
                  ? `${responseState.derivedCaseSummary.comfortRangeMin} – ${responseState.derivedCaseSummary.comfortRangeMax}`
                  : 'Pending'}
              </strong>
            </div>
            <div>
              <span className="interview-summary__term">Risk areas</span>
              <strong className="interview-summary__value">
                {responseState?.derivedCaseSummary.restrictedRegisters.join(', ') || 'None confirmed yet'}
              </strong>
            </div>
            <div>
              <span className="interview-summary__term">Collected answers</span>
              <strong className="interview-summary__value">
                {responseState?.collectedAnswers?.length ?? 0}
              </strong>
            </div>
          </div>

          <div className="new-case-actions">
            <Link href={caseId ? `/cases/${caseId}` : '/'} className="new-case-actions__button">
              <ArrowLeft className="new-case-actions__button-icon" />
              <span>Back To Case</span>
            </Link>
          </div>
        </aside>
      </div>
    </main>
  );
}
