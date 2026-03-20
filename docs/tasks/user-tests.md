# User Tests

Reference: [Tasks Index](./index.md)

**Quick Navigation:**
- [Task Overview](./overview.md) – Developer task assignments and parallelization
- [Task Briefs](./task-briefs/index.md) – Detailed implementation briefs
- [Architecture Features](../architecture/features.md) – Feature specifications

## Purpose

This file explains how a non-technical user can manually test the visible program state for each feature.
The instructions stay short and focus on what to click, what to enter, and what should happen next.

---

## F1. Case Entry {#ut-f1}

Goal for the user:
Open the app, see existing cases, and start or continue work.

Test path:

1. Open the start page.
2. Look for `Suggested case`, `Other cases`, and `Start New Case`.
3. Click one existing case.
4. Go back.
5. Click `Start New Case`.

Expected result:

- the start page loads without `404`
- existing cases are visible when they exist
- one suggested case is highlighted
- clicking an existing case opens its case page
- clicking `Start New Case` opens the new-case flow

---

## F2. Structured Interview Session {#ut-f2}

Goal for the user:
Answer a guided interview instead of typing random free text.

Test path:

1. Start a new case or open an existing case in interview state.
2. Click `Start Interview` or `Continue Interview`.
3. Answer the first questions.
4. Give one unclear answer once.

Expected result:

- questions appear one after another
- the interview feels guided and structured
- progress is visible
- an unclear answer causes a follow-up instead of silent guessing

---

## F3. Case Readiness And Persistence {#ut-f3}

Goal for the user:
See that confirmed interview data is saved and the case becomes ready for upload only when it is really complete.

Test path:

1. Finish an interview with clear answers.
2. Return to the case page.
3. Create another case with different answers.
4. Return to both case pages separately.

Expected result:

- the finished case shows the chosen instrument and saved constraints
- the case becomes `ready_for_upload` only when the required interview data is truly complete
- different cases stay separate from each other

---

## F4. MusicXML Upload Acceptance {#ut-f4}

Goal for the user:
Upload a supported score file to a ready case.

Test path:

1. Open a case that is `ready_for_upload`.
2. Use the upload area.
3. Select a valid `.musicxml`, `.xml`, or `.mxl` file.
4. Try one unsupported file type as a negative check.

Expected result:

- valid MusicXML-family files are accepted
- unsupported files are rejected with a clear message
- the upload is linked to the current case
- the page shows an initial processing state after upload

---

## F5. Score Parsing {#ut-f5}

Goal for the user:
See that the uploaded score is processed into a usable internal state.

Test path:

1. Upload a valid MusicXML file.
2. Wait for processing to move forward.
3. If available, try one malformed MusicXML file as a negative check.

Expected result:

- a valid file moves beyond the raw uploaded state
- a malformed file does not silently succeed
- parsing problems appear as a clear failure state, not as a broken page

---

## F6. Recommendation Context Assembly {#ut-f6}

Goal for the user:
Trust that the system combines case details and score details before making recommendations.

Test path:

1. Finish the interview.
2. Upload a score.
3. Wait for recommendation preparation.

Expected result:

- the system does not jump straight from upload to random recommendations
- recommendations only appear after the system has enough context
- if something important is missing, the process should not pretend to be complete

---

## F7. Recommendation Generation {#ut-f7}

Goal for the user:
Receive one or more proposed target ranges with confidence and warnings.

Test path:

1. Reach the recommendation stage after upload and processing.
2. Look at the recommendation area.
3. Compare the available options.

Expected result:

- at least one recommendation appears when the system has enough information
- confidence is visible
- warnings are visible when relevant
- blocked or low-confidence cases look clearly different from normal success

---

## F8. Recommendation Review And Selection {#ut-f8}

Goal for the user:
Review the options and choose one explicitly.

Test path:

1. Open the recommendation screen.
2. Read the primary and secondary recommendations.
3. Select one recommendation.

Expected result:

- the main option is clearly emphasized
- secondary options are still visible
- warnings and confidence remain visible during review
- selection is explicit and does not happen automatically just by viewing the page

---

## F8b. Safe Score Preview And Result Comparison {#ut-f8b}

Goal for the user:
View the uploaded score safely and later compare it with the transformed result.

Test path:

1. Open a case with an uploaded score.
2. Look for a score preview area.
3. If only the original is available, view the `Original` preview.
4. If a transformed result is available later, switch between `Original` and `Result`.

Expected result:

- the preview is read-only
- the preview does not behave like an editor
- the `Original` view appears when source preview is available
- the `Result` view only becomes usable when result preview is ready
- missing preview data shows a calm unavailable state instead of raw technical details

---

## F9. Deterministic Transformation {#ut-f9}

Goal for the user:
Start the actual transposition after choosing a recommendation.

Test path:

1. Select a recommendation.
2. Start the transformation step.
3. Wait for the next processing state.

Expected result:

- transformation starts only after explicit selection
- the system shows that work is in progress
- warnings appear if the transformation cannot adapt everything cleanly

---

## F10. Result Export {#ut-f10}

Goal for the user:
Get a transformed result prepared as a MusicXML output artifact.

Test path:

1. Let the transformation finish.
2. Wait for the result generation step.

Expected result:

- the system produces a result artifact after successful transformation
- export problems appear as a clear failure or warning state
- the app does not pretend the result is ready when export failed

---

## F11. Processing Status Visibility {#ut-f11}

Goal for the user:
Understand where the program currently is in the process.

Test path:

1. Move through upload, parsing, recommendation, transformation, and result steps.
2. Refresh the page once during a processing step if needed.

Expected result:

- the app shows clear states such as queued, parsing, transforming, completed, or failed
- the status remains understandable after refresh
- warnings and failures are shown in a calm, structured way

---

## F12. Result Download {#ut-f12}

Goal for the user:
Download the transformed MusicXML result.

Test path:

1. Open a case with a completed result.
2. Go to the result screen.
3. Click the download action.

Expected result:

- the download button is available only when the result is ready
- clicking download starts retrieval of the transformed file
- if result generation is not finished, normal download is not offered yet

---

## F13. Case Edit And Reset {#ut-f13}

Goal for the user:
Change or reset a case without creating a completely different workflow.

Test path:

1. Open an existing case.
2. Use the edit or reset action.
3. Return to the relevant earlier step.

Expected result:

- the case can be edited or reset intentionally
- the case does not become inconsistent
- the app clearly shows that recommendations or later results may need to be refreshed afterwards

---

## F14. Handle Stale Recommendation {#ut-f14}

Goal for the user:
See that old recommendations are no longer treated as valid when the case changes.

Test path:

1. Create or load recommendations.
2. Change the case constraints afterwards.
3. Return to the recommendation area.

Expected result:

- older recommendations are marked as stale
- the app does not silently continue with outdated recommendation data
- the user is guided toward regeneration instead of hidden reuse

---

## F15. Retryable Failure Recovery {#ut-f15}

Goal for the user:
Recover from failures that are safe to retry.

Test path:

1. Reach a retryable failure state.
2. Use the retry action if one is shown.

Expected result:

- retry is only shown when the backend says retry is allowed
- the retry action restarts the correct step
- non-retryable failures do not pretend to be retryable

---

## F16. Deployment And Environment Verification {#ut-f16}

Goal for the user:
Confirm that the deployed version still behaves like the tested workflow.

Test path:

1. Open the deployed app.
2. Load the main page.
3. Walk through one normal case flow from case selection to result retrieval.

Expected result:

- the frontend can reach the backend
- core pages load in the deployed environment
- the main user flow still behaves like the documented local MVP flow

---

## Usage Note

These user tests are intentionally short.
They are not a full QA script.
They are a quick way for a non-technical reviewer to check whether a feature is visible and behaves as expected.
