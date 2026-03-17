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

## External API

### `POST /interviews`

Purpose:
Start or continue the AI-guided questionnaire.

Contract shape:

- input: interview session identifier when continuing, latest user answer payload
- output: next question, collected profile state, completion status

Failure behavior:

- reject invalid session state
- reject malformed answer payloads
- return recoverable errors when the AI cannot classify an answer confidently

Ownership:
Backend API with AI interview service

Evolution:
The questionnaire contract should remain structured even if the conversation layer changes.

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

- input: multipart upload with MusicXML file and associated `transpositionCaseId`
- output: `scoreDocumentId`, format, validation status

Failure behavior:

- reject unsupported file types
- reject malformed MusicXML
- reject files above configured size limits

Ownership:
Backend API

Evolution:
Start with MusicXML-only support and extend through explicit format versioning later.

### `POST /recommendations`

Purpose:
Request AI-generated target range recommendations for an uploaded score.

Contract shape:

- input: `scoreDocumentId`, `transpositionCaseId`
- output: recommendation set with one or more target ranges and explanations

Failure behavior:

- reject unknown score IDs
- reject missing or incomplete case constraints
- return failed analysis status with typed explanation when recommendation cannot be produced reliably

Ownership:
Backend API with AI recommendation service

Evolution:
The recommendation payload may grow with confidence, rationale, and difficulty metadata.

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

### `GET /transformations/{id}`

Purpose:
Retrieve processing state and transformation outcome.

Contract shape:

- output: status, warnings, result identifiers, processing path summary

Failure behavior:

- return not found for unknown jobs
- return failed status with typed error details for processing failures

Ownership:
Backend API

Evolution:
New metadata should be backward compatible and additive.

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

- input: `CanonicalScore v1`, `TranspositionCaseConstraints v1`, instrument knowledge context
- output: one or more recommended target ranges, confidence metadata, explanation metadata

Failure behavior:

- low-confidence output should be marked and should not skip user confirmation
- model failure should stop recommendation generation rather than invent a range silently

Ownership:
AI recommendation service

Evolution:
The AI provider must remain replaceable behind this contract.
