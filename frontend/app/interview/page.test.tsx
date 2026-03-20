import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { within } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import InterviewPage from './page';
import { interviewsApi } from '@/shared/api/interviews';

vi.mock('@/shared/api/interviews', () => ({
  interviewsApi: {
    startOrContinueInterview: vi.fn(),
    getInterview: vi.fn(),
  },
}));

const replace = vi.fn();
let currentSearchParams = new URLSearchParams({
  caseId: 'case-123',
});

vi.mock('next/navigation', () => ({
  useRouter: () => ({
    replace,
  }),
  useSearchParams: () => currentSearchParams,
}));

describe('InterviewPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    currentSearchParams = new URLSearchParams({
      caseId: 'case-123',
    });
  });

  it('starts the interview and renders the first single-select question', async () => {
    vi.mocked(interviewsApi.startOrContinueInterview).mockResolvedValue({
      interviewId: 'interview-1',
      caseId: 'case-123',
      status: 'in_progress',
      nextQuestion: {
        id: 'instrument_identity',
        prompt: 'Which instrument should this transposition case target?',
        type: 'single_select',
        required: true,
        helpText: 'Pick the main instrument context so the later range checks stay grounded.',
        options: [
          { value: 'trumpet-bb', label: 'B-flat Trumpet' },
          { value: 'alto-sax-eb', label: 'E-flat Alto Saxophone' },
        ],
      },
      progress: {
        currentStep: 1,
        totalSteps: 4,
        percentComplete: 0,
      },
      lowConfidence: false,
      derivedCaseSummary: {
        caseStatus: 'interview_in_progress',
        instrumentIdentity: 'placeholder',
        difficultKeys: [],
        restrictedRegisters: [],
        comfortRangeMin: null,
        comfortRangeMax: null,
        notes: [],
        confirmedConstraintCount: 0,
      },
    });

    render(<InterviewPage />);

    await waitFor(() => {
      expect(interviewsApi.startOrContinueInterview).toHaveBeenCalledWith({ caseId: 'case-123' });
    });

    expect(await screen.findByText('Which instrument should this transposition case target?')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /b-flat trumpet/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /submit answer/i })).toBeDisabled();
  });

  it('submits answers and renders the next multi-select question', async () => {
    vi.mocked(interviewsApi.startOrContinueInterview)
      .mockResolvedValueOnce({
        interviewId: 'interview-1',
        caseId: 'case-123',
        status: 'in_progress',
        nextQuestion: {
          id: 'instrument_identity',
          prompt: 'Which instrument should this transposition case target?',
          type: 'single_select',
          required: true,
          helpText: null,
          options: [{ value: 'trumpet-bb', label: 'B-flat Trumpet' }],
        },
        progress: {
          currentStep: 1,
          totalSteps: 4,
          percentComplete: 0,
        },
        lowConfidence: false,
        derivedCaseSummary: {
          caseStatus: 'interview_in_progress',
          instrumentIdentity: 'placeholder',
          difficultKeys: [],
          restrictedRegisters: [],
          comfortRangeMin: null,
          comfortRangeMax: null,
          notes: [],
          confirmedConstraintCount: 0,
        },
      })
      .mockResolvedValueOnce({
        interviewId: 'interview-1',
        caseId: 'case-123',
        status: 'in_progress',
        nextQuestion: {
          id: 'challenge_areas',
          prompt: 'Which areas usually feel risky or tiring for this player?',
          type: 'multi_select',
          required: false,
          helpText: 'Choose all that apply. Leave it empty if nothing stands out.',
          options: [{ value: 'high_register', label: 'High register' }],
        },
        progress: {
          currentStep: 2,
          totalSteps: 4,
          percentComplete: 25,
        },
        lowConfidence: false,
        derivedCaseSummary: {
          caseStatus: 'interview_in_progress',
          instrumentIdentity: 'trumpet-bb',
          difficultKeys: [],
          restrictedRegisters: [],
          comfortRangeMin: null,
          comfortRangeMax: null,
          notes: [],
          confirmedConstraintCount: 1,
        },
      });

    render(<InterviewPage />);

    const option = await screen.findByRole('button', { name: /b-flat trumpet/i });
    fireEvent.click(option);
    expect(screen.getByRole('button', { name: /submit answer/i })).not.toBeDisabled();
    fireEvent.click(screen.getByRole('button', { name: /submit answer/i }));

    await waitFor(() => {
      expect(interviewsApi.startOrContinueInterview).toHaveBeenLastCalledWith({
        caseId: 'case-123',
        interviewId: 'interview-1',
        questionId: 'instrument_identity',
        answer: {
          selectedOption: 'trumpet-bb',
        },
      });
    });

    expect(await screen.findByText('Which areas usually feel risky or tiring for this player?')).toBeInTheDocument();
  });

  it('shows the structured low-confidence follow-up banner', async () => {
    vi.mocked(interviewsApi.startOrContinueInterview)
      .mockResolvedValueOnce({
        interviewId: 'interview-1',
        caseId: 'case-123',
        status: 'in_progress',
        nextQuestion: {
          id: 'additional_context',
          prompt: 'Any extra context about the player or the arrangement?',
          type: 'note_text',
          required: false,
          helpText: null,
          placeholder: 'Optional notes',
          options: [],
        },
        progress: {
          currentStep: 4,
          totalSteps: 4,
          percentComplete: 75,
        },
        lowConfidence: false,
        derivedCaseSummary: {
          caseStatus: 'interview_in_progress',
          instrumentIdentity: 'trumpet-bb',
          difficultKeys: [],
          restrictedRegisters: [],
          comfortRangeMin: 'G3',
          comfortRangeMax: 'D5',
          notes: [],
          confirmedConstraintCount: 3,
        },
      })
      .mockResolvedValueOnce({
        interviewId: 'interview-1',
        caseId: 'case-123',
        status: 'awaiting_follow_up',
        nextQuestion: {
          id: 'additional_context_follow_up',
          prompt: 'Your note sounded uncertain. What should the system avoid assuming?',
          type: 'note_text',
          required: true,
          helpText: 'Clarify the uncertain part so the case keeps confirmed and inferred constraints separate.',
          placeholder: 'Avoid assuming an extended upper register.',
          options: [],
        },
        progress: {
          currentStep: 4,
          totalSteps: 4,
          percentComplete: 75,
        },
        lowConfidence: true,
        derivedCaseSummary: {
          caseStatus: 'interview_in_progress',
          instrumentIdentity: 'trumpet-bb',
          difficultKeys: [],
          restrictedRegisters: [],
          comfortRangeMin: 'G3',
          comfortRangeMax: 'D5',
          notes: ['not sure about the upper register'],
          confirmedConstraintCount: 3,
        },
      });

    render(<InterviewPage />);

    const textArea = await screen.findByLabelText('Interview note');
    fireEvent.change(textArea, { target: { value: 'not sure about the upper register' } });
    fireEvent.click(screen.getByRole('button', { name: /submit answer/i }));

    expect(await screen.findByText('Clarification required')).toBeInTheDocument();
    expect(screen.getByText(/The previous answer sounded uncertain/i)).toBeInTheDocument();
  });

  it('renders collected answers when the session is resumed through interviewId', async () => {
    currentSearchParams = new URLSearchParams({
      caseId: 'case-123',
      interviewId: 'interview-1',
    });

    vi.mocked(interviewsApi.getInterview).mockResolvedValue({
      interviewId: 'interview-1',
      caseId: 'case-123',
      status: 'in_progress',
      currentQuestion: {
        id: 'challenge_areas',
        prompt: 'Which areas usually feel risky or tiring for this player?',
        type: 'multi_select',
        required: false,
        helpText: null,
        options: [{ value: 'high_register', label: 'High register' }],
      },
      progress: {
        currentStep: 2,
        totalSteps: 4,
        percentComplete: 25,
      },
      lowConfidence: false,
      collectedAnswers: [
        {
          questionId: 'instrument_identity',
          questionType: 'single_select',
          value: { selectedOption: 'trumpet-bb' },
          lowConfidenceFlag: false,
          answeredAt: '2024-01-15T10:00:00Z',
        },
      ],
      derivedCaseSummary: {
        caseStatus: 'interview_in_progress',
        instrumentIdentity: 'trumpet-bb',
        difficultKeys: [],
        restrictedRegisters: [],
        comfortRangeMin: null,
        comfortRangeMax: null,
        notes: [],
        confirmedConstraintCount: 1,
      },
    });

    render(<InterviewPage />);

    await waitFor(() => {
      expect(interviewsApi.getInterview).toHaveBeenCalledWith('interview-1');
    });

    expect(await screen.findByText('Collected answers')).toBeInTheDocument();
    const summarySection = screen.getByText('Collected answers').closest('div');
    expect(summarySection).not.toBeNull();
    expect(within(summarySection as HTMLElement).getByText('1')).toBeInTheDocument();
  });

  it('does not show the success completion message when the interview ends without upload-ready constraints', async () => {
    vi.mocked(interviewsApi.startOrContinueInterview).mockResolvedValue({
      interviewId: 'interview-1',
      caseId: 'case-123',
      status: 'completed',
      nextQuestion: null,
      progress: {
        currentStep: 4,
        totalSteps: 4,
        percentComplete: 100,
      },
      lowConfidence: false,
      collectedAnswers: [],
      derivedCaseSummary: {
        caseStatus: 'interview_in_progress',
        instrumentIdentity: 'flute',
        difficultKeys: [],
        restrictedRegisters: [],
        comfortRangeMin: 'no',
        comfortRangeMax: 'no',
        notes: ['no'],
        confirmedConstraintCount: 1,
      },
    });

    render(<InterviewPage />);

    expect(await screen.findByText('Interview data still needs clarification')).toBeInTheDocument();
    expect(
      screen.getByText(/the confirmed constraints are still not sufficient for upload readiness/i)
    ).toBeInTheDocument();
    expect(screen.queryByText('Interview session complete')).not.toBeInTheDocument();
  });

  it('prioritizes edit-mode restart over a stale interviewId in the URL', async () => {
    currentSearchParams = new URLSearchParams({
      caseId: 'case-123',
      interviewId: 'stale-interview-1',
      mode: 'edit',
    });

    vi.mocked(interviewsApi.startOrContinueInterview).mockResolvedValue({
      interviewId: 'interview-edit-fresh',
      caseId: 'case-123',
      status: 'in_progress',
      nextQuestion: {
        id: 'instrument_identity',
        prompt: 'Which instrument should this transposition case target?',
        type: 'single_select',
        required: true,
        helpText: 'Pick the main instrument context so the later range checks stay grounded.',
        options: [{ value: 'flute', label: 'Flute' }],
      },
      progress: {
        currentStep: 1,
        totalSteps: 4,
        percentComplete: 0,
      },
      lowConfidence: false,
      derivedCaseSummary: {
        caseStatus: 'interview_in_progress',
        instrumentIdentity: 'placeholder',
        difficultKeys: [],
        restrictedRegisters: [],
        comfortRangeMin: null,
        comfortRangeMax: null,
        notes: [],
        confirmedConstraintCount: 0,
      },
    });

    render(<InterviewPage />);

    await waitFor(() => {
      expect(interviewsApi.startOrContinueInterview).toHaveBeenCalledWith({
        caseId: 'case-123',
        restart: true,
      });
    });
    expect(interviewsApi.getInterview).not.toHaveBeenCalled();
    expect(replace).toHaveBeenCalledWith('/interview?caseId=case-123&interviewId=interview-edit-fresh');
    expect(await screen.findByText('Which instrument should this transposition case target?')).toBeInTheDocument();
  });
});
