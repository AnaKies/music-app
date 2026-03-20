# Interfaces

Reference: [Architecture Index](./index.md)
Related context: [System Context](./system-context.md)
Related modules: [Module Design](./module-design.md)

## Document Role

This document defines contract boundaries only:

- external API endpoints
- internal module-to-module contracts
- input and output shapes
- failure behavior
- ownership
- versioning expectations

System flow and product behavior belong in [System Context](./system-context.md).
Module responsibilities belong in [Module Design](./module-design.md).

## Interface Flow Diagram

```mermaid
flowchart LR
    FE[Frontend Application] --> I1[POST /interviews]
    FE --> C1[POST /cases]
    FE --> C2[GET /cases/{id}]
    FE --> S1[POST /scores]
    FE --> S2[GET /scores/{id}]
    FE --> R1[POST /recommendations]
    FE --> T1[POST /transformations]
    FE --> T2[GET /transformations/{id}]
    FE --> D1[GET /scores/{id}/download]

    I1 --> AIQ[AI Interview Service]
    C1 --> CASE[Transposition Case Service]
    C2 --> CASE
    S1 --> PARSER[Score Parser]
    S2 --> SCORESTATE[Score Processing Status]
    R1 --> AIR[AI Recommendation Service]
    T1 --> TX[Transformation Engine]
    T2 --> JOB[Processing Job State]
    D1 --> STORE[Artifact Storage]
```

Diagram purpose:
Show how the frontend-facing API contracts map onto the major internal service boundaries behind them.

What to read from it:
The frontend talks only to API contracts, while the backend routes those contracts to specialized modules for interviewing, case management, parsing, recommendation, execution, job tracking, and artifact delivery.

Why it belongs here:
This file owns contract boundaries and is the right place to visualize how external endpoints align with internal interface ownership.

## External API

### `POST /interviews`

Purpose:
Start or continue the AI-guided questionnaire.

Contract shape:

- input: interview session identifier when continuing, latest structured user answer payload
- output: next question object, collected profile state, completion status

Recommended question object shape:

- `questionId`
- `prompt`
- `questionType` such as `single_select`, `multi_select`, `note_input`, `range_input`, or `free_text`
- `options` when the question is selection-based
- `validationRules`
- `isRequired`
- `helpText` when clarification is needed

Safety note:
Structured question types should be preferred over free-form collection whenever they are sufficient for product behavior.
Free-text questions should remain exceptional and should not become the default persistence shape for user constraints.

Recommended selection option shape:

- `label`
- `value`
- optional `description`

Recommended answer payload shape:

- `questionId`
- `answerType`
- `value`
- optional `clientValidationState` when the frontend wants to report local validation results without making it a required contract field

Failure behavior:

- reject invalid session state
- reject malformed answer payloads
- return recoverable errors when the AI cannot classify an answer confidently

Ownership:
Backend API with AI interview service

Evolution:
The questionnaire contract should remain structured even if the conversation layer changes.
The contract should evolve toward more structured fields rather than toward broader free-text persistence.

### `GET /interviews/{id}`

Purpose:
Retrieve the current structured interview state and derived transposition case summary.

Contract shape:

- output: interview status, collected answers, derived case summary

Failure behavior:

- return not found for unknown interview sessions

Ownership:
Backend API

Evolution:
Additional derived fields should be additive.

### `POST /cases`

Purpose:
Create a new transposition case or explicitly reset an existing one.

Contract shape:

- input: instrument identity, optional existing case action such as `reset`
- output: `transpositionCaseId`, status, case summary

Failure behavior:

- reject unknown reset targets
- reject conflicting case actions

Ownership:
Backend API

Evolution:
The case model may later support archive and clone behavior.

### `GET /cases/{id}`

Purpose:
Retrieve the active constraints and state for a transposition case.

Contract shape:

- output: case summary, active constraints, linked score count, status

Recommended case status values:

- `new`
- `interview_in_progress`
- `ready_for_upload`
- `recommendation_ready`
- `completed`
- `archived`

Failure behavior:

- return not found for unknown cases

Ownership:
Backend API

Evolution:
Additional summary fields should be additive.

### `POST /scores`

Purpose:
Upload an original score document.

Contract shape:

- input: multipart upload with MusicXML-family file (`.musicxml`, `.xml`, or compressed `.mxl`) and associated `transpositionCaseId`
- output: `scoreDocumentId`, format, accepted status, initial processing snapshot

Failure behavior:

- reject unsupported file types
- reject malformed MusicXML
- reject files above configured size limits

Ownership:
Backend API

Evolution:
Start with MusicXML-only support and extend through explicit format versioning later.

Runtime note:
Parsing and recommendation preparation may continue through an asynchronous worker path after upload acceptance. Frontend state should rely on the score read contract for durable progress visibility.

### `GET /scores/{id}`

Purpose:
Retrieve the current status snapshot for an uploaded score document.

Contract shape:

- output: `scoreDocumentId`, processing status, active `transpositionCaseId`, recommendation snapshot summary, stale flag when applicable, warnings, failure details, available artifact references, normalized presentation metadata, and preview read models

Recommended score processing status values:

- `uploaded`
- `queued`
- `parsing`
- `recommendation_pending`
- `recommendation_ready`
- `transforming`
- `completed`
- `failed`

Recommended preview read-model shape:

- `sourcePreview`
- `resultPreview`

Recommended preview object fields:

- `availability` with values `ready`, `not_ready`, `unavailable`, or `failed`
- `artifactRole` with values `source` or `result`
- `rendererFormat` such as `musicxml_preview`
- `pageCount` when known
- `revisionToken` for cache-safe viewer refresh
- `safeSummary`
- `failureCode` when `availability` is `failed`
- `failureSeverity`
- `previewAccess` as a preview-only reference or token, never a raw storage path or download URL

Recommended presentation metadata fields:

- `severity` for warning and failure rendering
- `isRetryable`
- `confidence` when recommendation state is involved
- `safeSummary` for concise user-facing status explanation without leaking raw internal errors
- `previewMode` when the frontend needs to distinguish source-only, result-only, and comparison-capable preview states

Safety note:
Read models must not expose raw provider output, raw prompts, internal storage paths, or raw backend exception text through user-facing status contracts.

Failure behavior:

- return not found for unknown score IDs
- return typed failure metadata when the score flow has failed

Ownership:
Backend API

Evolution:
Additional score-summary metadata should be additive and must preserve the stable status meanings used by frontend polling.

Preview note:
Score read models may expose preview-readiness and safe preview metadata, but they must not expose raw storage URIs, editable file handles, or any contract that bypasses backend-owned access control and safety normalization.

### `POST /recommendations`

Purpose:
Request AI-generated target range recommendations for an uploaded score.

Contract shape:

- input: `scoreDocumentId`, `transpositionCaseId`
- output: recommendation set with one or more target ranges and explanations

Recommended recommendation item shape:

- `recommendationId`
- `label`
- `targetRange`
- `recommendedKey` when applicable
- `confidence`
- `summaryReason`
- `warnings`
- `isPrimary`

Failure behavior:

- reject unknown score IDs
- reject missing or incomplete case constraints
- return failed analysis status with typed explanation when recommendation cannot be produced reliably

Ownership:
Backend API with AI recommendation service

Evolution:
The recommendation payload may grow with confidence, rationale, and difficulty metadata, but normal payload fields must remain presentation-safe and must not expose raw provider text.

Runtime note:
Recommendation generation may be fulfilled through an asynchronous worker path as long as status visibility and result traceability remain consistent with the documented job model and the score-status read contract.

### `POST /transformations`

Purpose:
Start a deterministic transformation job for a user-selected recommended range.

Contract shape:

- input: `scoreDocumentId`, `recommendationId` or selected `targetRange`, optional mode flags
- output: `transformationJobId`, status

Failure behavior:

- reject unknown score IDs
- reject unknown recommendation IDs
- reject missing or conflicting target parameters
- reject transformations that violate validated constraint boundaries

Ownership:
Backend API

Evolution:
Additional execution options should be additive and must not change the meaning of stored recommendations.

Runtime note:
Transformation execution is expected to run through an asynchronous worker path rather than blocking the request-response cycle.

### `GET /transformations/{id}`

Purpose:
Retrieve processing state and transformation outcome.

Contract shape:

- output: status, warnings, result identifiers, processing path summary

Recommended presentation metadata fields:

- `severity`
- `isRetryable`
- `safeSummary`

Safety note:
Transformation status responses must remain presentation-safe and must not leak raw backend diagnostics into the frontend contract.

Failure behavior:

- return not found for unknown jobs
- return failed status with typed error details for processing failures

Ownership:
Backend API

Evolution:
New metadata should be backward compatible and additive.

Runtime note:
This endpoint is the public read path for worker-driven job progress and final execution outcome.

### `GET /scores/{id}/download`

Purpose:
Download original or transformed score artifacts.

Contract shape:

- input: score identifier and artifact selector
- output: file stream

Failure behavior:

- return not found for missing artifacts
- return forbidden if access rules are introduced later

Ownership:
Backend API

Evolution:
This interface may later support PDF or MIDI exports in addition to MusicXML.

Frontend note:
For the MVP, download of MusicXML is required. Direct print support is optional and may be implemented as a frontend convenience feature rather than a backend-specific output format.

### `GET /scores/{id}/preview`

Purpose:
Retrieve or authorize read-only preview access for the source score.

Contract shape:

- output: preview session metadata for the source artifact only
- never returns the downloadable artifact itself
- fails with typed preview states such as `not_ready`, `unsupported`, or `failed`

Failure behavior:

- return not found for unknown scores
- return a typed unavailable state when the requested source preview cannot be produced
- return failed safely when preview generation or preview retrieval cannot complete

Ownership:
Backend API

Evolution:
The preview contract may evolve in a backward-compatible way, but it must remain read-only and must not become an editing or raw artifact access path.

Safety note:
Preview responses must remain presentation-safe. They must not expose internal storage paths, unbounded raw diagnostics, or mutable artifact references.

### `GET /transformations/{id}/preview`

Purpose:
Retrieve or authorize read-only preview access for the transformed result.

Contract shape:

- output: preview session metadata for the result artifact only
- preview access is distinct from download access and must not imply export delivery
- fails with typed preview states such as `not_ready`, `not_generated`, or `failed`

Failure behavior:

- return not found for unknown transformations
- return a typed unavailable state when the result artifact does not exist yet
- return failed safely when preview generation or preview retrieval cannot complete

Ownership:
Backend API

Evolution:
The result-preview contract may evolve in a backward-compatible way, but it must remain read-only and must not become a download or editing backchannel.

Safety note:
Result-preview responses must remain presentation-safe and must not expose raw storage paths, raw renderer diagnostics, or download-capable links.

## Internal Contracts

### AI Interview Service to Transposition Case Constraints

Purpose:
Transform conversational answers into case constraints for later recommendation logic.

Contract shape:

- input: interview state and user answers
- output: `TranspositionCaseConstraints v1`

Failure behavior:

- low-confidence interpretation should trigger follow-up questions instead of silent guessing

Ownership:
AI interview service

Evolution:
The case constraint schema must be explicitly versioned.

### AI Context Contract

Purpose:
Define the structured context that backend modules must provide to AI services so AI behavior does not depend on implicit model memory alone.

Contract shape:

- input:
  - `InterviewState v1` for ongoing interview turns
  - `TranspositionCase v1` user-confirmed constraints
  - `InferredConstraintSet v1` AI-derived but not yet fully trusted constraints when available
  - `InstrumentProfile v1` and instrument knowledge fields relevant to range, transposition, and key suitability
  - `CanonicalScoreSummary v1` for recommendation generation
- output:
  - schema-constrained interview updates or recommendation payloads only

Failure behavior:

- reject incomplete context for recommendation generation when required score or case inputs are missing
- low-confidence AI outputs must remain explicitly marked and must not be promoted to confirmed constraints silently

Ownership:
Backend API and AI services jointly, with backend owning validation and payload assembly

Evolution:
The context contract should evolve through additive fields and explicit versioning rather than undocumented prompt changes.

### Parser to Canonical Score Model

Purpose:
Normalize uploaded MusicXML into a stable internal representation.

Contract shape:

- input: validated MusicXML document
- output: `CanonicalScore v1`

Failure behavior:

- fail fast on parse errors
- return structured validation errors for unsupported constructs

Ownership:
Parser module

Evolution:
The canonical model must be explicitly versioned.

### Canonical Score Model to Transformation Engine

Purpose:
Provide normalized score data for deterministic transposition execution.

Contract shape:

- input: `CanonicalScore v1`, selected target range, instrument profile
- output: transformed score sections, warnings, rule metadata

Failure behavior:

- return typed warnings for out-of-range passages
- return failure if required source data is incomplete

Ownership:
Transformation engine

Evolution:
Rule metadata can grow, but the score contract should remain stable within a version.

### Canonical Score Model to AI Recommendation Service

Purpose:
Request recommended target ranges for a parsed score and active transposition case.

Contract shape:

- input: `CanonicalScore v1`, `TranspositionCaseConstraints v1`, `InferredConstraintSet v1` when available, instrument knowledge context
- output: one or more recommended target ranges, confidence metadata, explanation metadata

Failure behavior:

- low-confidence output should be marked and should not skip user confirmation
- model failure should stop recommendation generation rather than invent a range silently

Ownership:
AI recommendation service

Evolution:
The AI provider must remain replaceable behind this contract.
