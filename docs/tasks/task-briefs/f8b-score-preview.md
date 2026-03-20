# Task Briefs F8b

Reference: [Task Briefs Index](./index.md)
Related overview: [Overview](../overview.md)
Related features: [Architecture Features](../../architecture/features.md)

## F8b. Safe Score Preview And Result Comparison

Architecture note:
The preview boundary, placement in the workflow, and safety constraints for F8b are already defined in the architecture documents. The delivery tasks below implement against that approved architecture and do not reopen it as an in-feature task.

### Backend-25a

Objective:
Expose source-score preview availability and safe preview metadata.

Context:
The frontend should not guess whether an uploaded score can be previewed.

Deliverable:
A backend-readable field or endpoint that tells the frontend whether source preview is available and safe to request.

Dependencies:
Approved F8b architecture boundary.

Acceptance criteria:

- source preview availability is explicit
- preview metadata stays presentation-safe
- preview does not expose raw storage paths
- preview metadata includes explicit artifact role, availability state, safe summary, and preview-only access semantics

Backend preview metadata must include, at minimum:

- explicit artifact role `source` or `result`
- explicit availability state
- typed failure code when preview is unavailable because of an error
- presentation-safe summary text
- preview-only access reference or token
- optional viewer hints such as page count or renderer format

Preview metadata must not include:

- raw storage paths
- raw export locations
- download URLs
- raw parser or renderer diagnostics

Out of scope:
Rendering the score.

Suggested verification:
Read-model or route contract test.

### Backend-25b

Objective:
Expose result-score preview availability and safe preview metadata.

Context:
Result preview should only become visible when a transformed or exported score artifact is actually available.

Deliverable:
A backend-readable field or endpoint that exposes result-preview readiness and typed preview failure states.

Dependencies:
Approved F8b architecture boundary and the approved result-preview contract after F10 result export.

Acceptance criteria:

- result preview readiness is explicit
- unavailable results fail safely
- preview and download semantics stay distinct
- result preview relies on its own preview contract rather than the normal download path

Out of scope:
Download delivery itself.

Suggested verification:
Contract test with ready and not-ready states.

### Frontend-17a

Objective:
Create the preview workspace scaffold.

Context:
Score preview should fit into the existing staged workflow rather than appearing as an isolated ad hoc page.

Deliverable:
A screen or section shell for score preview with room for source, result, loading, and failure states.

Dependencies:
Approved F8b architecture boundary.

Acceptance criteria:

- preview area exists
- loading and empty states are understandable
- layout remains usable on desktop and mobile
- preview is documented as a dedicated panel inside the existing workspace shell rather than a detached standalone tool

Out of scope:
Actual score rendering.

Suggested verification:
Render test and manual route check.

### Frontend-17b

Objective:
Add source-score preview rendering.

Context:
The user should be able to confirm which score was uploaded before trusting later recommendation or transformation steps.

Deliverable:
A read-only source-preview view driven by backend preview metadata.

Dependencies:
Backend-25a and Frontend-17a.

Acceptance criteria:

- uploaded score can be viewed when available
- preview failure is shown calmly and safely
- no raw internal artifact details are exposed
- allowed interactions are limited to viewport navigation such as scroll, page movement, and optional zoom

Out of scope:
Result comparison.

Suggested verification:
UI test with source-preview-ready and source-preview-failed fixtures.

### Frontend-17c

Objective:
Add result-score preview rendering.

Context:
The user should be able to inspect the transformed result before or alongside download.

Deliverable:
A read-only result-preview view driven by backend preview metadata.

Dependencies:
Backend-25b and Frontend-17a.

Acceptance criteria:

- result score can be viewed when ready
- not-ready and failed states are clear
- result preview does not replace the primary download path
- the result workspace keeps download as the main completion action

Out of scope:
Download behavior.

Suggested verification:
UI test with ready and not-ready result fixtures.

### Frontend-17d

Objective:
Add the `Original` versus `Result` toggle or comparison mode.

Context:
The MVP needs a simple comparison affordance without turning the preview into a full notation diff tool.

Deliverable:
A toggle, segmented control, or equivalent comparison switch between source and result views.

Dependencies:
Backend-25a, Backend-25b, Frontend-17b, and Frontend-17c.

Acceptance criteria:

- the user can switch between `Original` and `Result`
- the current mode is explicit
- comparison remains read-only and simple
- default mode is `Original` until result preview is ready
- `Result` stays visible but disabled when result preview is not ready

Comparison uses two independent read-only preview models, one for `Original` and one for `Result`.
The comparison control switches viewer context only.
It does not create a merged diff artifact, note-level comparison payload, or editable combined score state.

Out of scope:
Note-level diff highlighting and editing.

Suggested verification:
Interaction test.

### Safety-5a

Objective:
Review that preview remains read-only and presentation-safe.

Context:
Preview introduces a user-facing rendering of uploaded and generated score artifacts, which must not bypass the MVP safety model.

Deliverable:
A short review confirming the preview boundaries or flagging required restrictions.

Dependencies:
Approved F8b architecture boundary and the implemented preview contract.

Acceptance criteria:

- raw internal file paths are not exposed
- no editable or misleading workflow is introduced
- failures use typed user-facing summaries
- preview access remains distinct from download access

Out of scope:
Validation of the notation engine internals.

Suggested verification:
Safety review note.

### Test-28a

Objective:
Add a UI test for source-score preview.

Context:
The source preview is the first user-visible confirmation that the uploaded score is the expected one.

Deliverable:
A UI test that verifies source preview readiness, rendering, and empty or unavailable states.

Dependencies:
Frontend-17b.

Acceptance criteria:

- source preview renders when available
- unavailable state is visible
- test fails if raw internal details leak into the UI
- test covers the documented read-only viewer mode

Out of scope:
Transformation result behavior.

Suggested verification:
Screen test with preview fixtures.

### Test-28b

Objective:
Add a UI test for result-score preview and preview failure states.

Context:
The user must be able to distinguish between not-yet-ready, available, and failed result-preview states.

Deliverable:
A UI test covering result preview rendering, toggle behavior, and safe failure handling.

Dependencies:
Frontend-17c and Frontend-17d.

Acceptance criteria:

- result preview renders when ready
- toggle behavior is explicit
- failures stay presentation-safe
- the test fails if preview and download semantics collapse into one action

Out of scope:
Download artifact retrieval.

Suggested verification:
Screen interaction test.
