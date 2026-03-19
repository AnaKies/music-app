'use client';

import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { ArrowLeft, CheckCircle2, Circle } from 'lucide-react';

export default function NewCaseFlowPage() {
  const searchParams = useSearchParams();
  const caseId = searchParams.get('caseId');
  const steps = [
    {
      title: 'Create the case shell',
      description: 'The user has left the case overview and entered a dedicated path for creating a new transposition case.',
      status: 'active'
    },
    {
      title: 'Collect interview constraints',
      description: 'A later step will connect this route to the structured interview flow from F2.',
      status: 'pending'
    },
    {
      title: 'Mark the case ready for upload',
      description: 'A later step will continue into case persistence and upload gating.',
      status: 'pending'
    }
  ];

  return (
    <main className="new-case-page">
      <header className="new-case-hero">
        <p className="new-case-hero__eyebrow">
          F1 · New Case Path
        </p>
        <h1 className="new-case-hero__title">
          The new-case flow has started.
        </h1>
        <p className="new-case-hero__description">
          This route-level scaffold proves that the case entry screen can transition 
          into a dedicated new-case path without implementing the interview yet.
        </p>
      </header>

      <section>
        <div className="new-case-flow">
          {steps.map((step, index) => (
            <article 
              key={index} 
              className={`new-case-step ${step.status === 'active' ? 'new-case-step--active' : ''}`}
            >
              <div className="new-case-step__icon">
                {step.status === 'active' ? (
                  <CheckCircle2 className="new-case-step__icon-symbol new-case-step__icon-symbol--active" />
                ) : (
                  <Circle className="new-case-step__icon-symbol" />
                )}
              </div>
              <div>
                <span className="new-case-step__state">
                  {step.status === 'active' ? 'Current step' : 'Next step'}
                </span>
                <h3 className="new-case-step__title">
                  {step.title}
                </h3>
                <p className="new-case-step__description">
                  {step.description}
                </p>
              </div>
            </article>
          ))}
        </div>
      </section>

      <div className="new-case-actions">
        {caseId ? (
          <Link
            href={`/interview?caseId=${caseId}`}
            className="new-case-actions__button new-case-actions__button--primary"
          >
            <span>Start Interview</span>
          </Link>
        ) : null}
        <Link 
          href="/" 
          className="new-case-actions__button"
        >
          <ArrowLeft className="new-case-actions__button-icon" />
          <span>Back To Cases</span>
        </Link>
      </div>
    </main>
  );
}
