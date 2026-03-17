# Data Model

Reference: [Architecture Index](./index.md)
Related modules: [Module Design](./module-design.md)
Related context: [System Context](./system-context.md)

## Modeling Principle

The system separates persistent transposition case constraints, structured instrument knowledge, uploaded artifacts, normalized musical structure, recommendation outputs, transformation requests, and generated results.
This keeps conversational intake, reusable case state, file handling, recommendation logic, and deterministic execution independent.

## Core Entities

### ScoreDocument

Purpose:
Represent an uploaded or generated file artifact.

Key fields:

- `id`
- `type` such as `original` or `transformed`
- `format`
- `storageUri`
- `checksum`
- `createdAt`

Lifecycle:
Created on upload or export.
Never mutated in place after persistence.

Operational notes:
Original and transformed artifacts should always be stored separately.

### CanonicalScore

Purpose:
Represent the normalized internal music structure.

Key fields:

- `id`
- `schemaVersion`
- `scoreDocumentId`
- `parts`
- `measures`
- `notes`
- `rests`
- `clefs`
- `keySignatures`
- `timeSignatures`
- `tempo`

Lifecycle:
Created after parsing.
May be regenerated when parser logic evolves.

Operational notes:
This model is the source of truth for transformation logic, not the raw MusicXML.

### InstrumentProfile

Purpose:
Describe the musical and notation constraints of a target instrument.

Key fields:

- `id`
- `name`
- `transposition`
- `writtenRangeMin`
- `writtenRangeMax`
- `soundingRangeMin`
- `soundingRangeMax`
- `preferredClefs`

Lifecycle:
Managed as reference data.

Operational notes:
Profiles should be versioned carefully because transformation behavior depends on them.

### TranspositionCase

Purpose:
Represent a persistent user and instrument context that can be reused across multiple score uploads.

Key fields:

- `id`
- `userId`
- `instrumentProfileId`
- `highestPlayableTone`
- `lowestPlayableTone`
- `restrictedTones`
- `restrictedRegisters`
- `difficultKeys`
- `preferredKeys`
- `comfortRangeMin`
- `comfortRangeMax`
- `status`
- `createdAt`
- `updatedAt`

Lifecycle:
Created during the interview flow and reused across multiple uploads until the user resets, archives, or replaces it.

Operational notes:
This case captures the playable reality of a specific user and instrument setup, not just the general capability of an instrument.

### TransformationRequest

Purpose:
Represent a user request to execute a deterministic conversion using a selected recommendation.

Key fields:

- `id`
- `sourceScoreDocumentId`
- `transpositionCaseId`
- `selectedRecommendationId`
- `targetRange`
- `mode`
- `requestedAt`

Lifecycle:
Created when a user starts a conversion job.

Operational notes:
The request record should preserve the exact processing intent for auditability.

### RangeRecommendation

Purpose:
Represent an AI-generated recommendation set for score transposition targets.

Key fields:

- `id`
- `scoreDocumentId`
- `transpositionCaseId`
- `recommendedRanges`
- `recommendedKeys`
- `explanations`
- `confidence`
- `createdAt`

Lifecycle:
Created after score analysis and referenced during user selection.

Operational notes:
Recommendations may contain multiple valid target ranges rather than a single forced answer.

### ProcessingJob

Purpose:
Track execution state and runtime outcomes.

Key fields:

- `id`
- `transformationRequestId`
- `status`
- `startedAt`
- `finishedAt`
- `processingPath`
- `errorCode`
- `warningCount`

Lifecycle:
Created at job start and updated until completion.

Operational notes:
Jobs should be observable without requiring direct access to generated files.

### TransformationResult

Purpose:
Represent the outcome of a completed conversion.

Key fields:

- `id`
- `processingJobId`
- `outputScoreDocumentId`
- `changedMeasures`
- `warnings`
- `confidence`

Lifecycle:
Created after successful or partially successful transformation.

Operational notes:
Confidence should be used only as advisory metadata, not as the only quality signal.

## Data Relationship Diagram

```mermaid
erDiagram
    ScoreDocument ||--o{ CanonicalScore : source_for
    InstrumentProfile ||--o{ TranspositionCase : baseline_for
    ScoreDocument ||--o{ RangeRecommendation : analyzed_as
    TranspositionCase ||--o{ ScoreDocument : groups
    TranspositionCase ||--o{ RangeRecommendation : guides
    ScoreDocument ||--o{ TransformationRequest : input_for
    TranspositionCase ||--o{ TransformationRequest : selected_for
    RangeRecommendation ||--o{ TransformationRequest : selected_from
    TransformationRequest ||--|| ProcessingJob : creates
    ProcessingJob ||--|| TransformationResult : produces
    TransformationResult }o--|| ScoreDocument : exports_as
```

Diagram purpose:
Show the core persistence entities and the relationships that connect reusable cases, uploaded scores, recommendations, execution requests, and generated results.

What to read from it:
The model separates reusable user/instrument context from uploaded files, AI recommendation outputs, execution tracking, and final artifacts so each lifecycle can evolve independently.

Why it belongs here:
This file owns the persistent entities, their lifecycle role, and their relationship structure.

## Consistency Rules

- A transformed file must always retain a reference to the original input request.
- A processing job must not overwrite the original artifact.
- Canonical score schema versioning must be explicit.
- AI-generated recommendations must remain attributable through recommendation and processing metadata.
- Transposition case constraints must persist across multiple uploads until the user resets or replaces the case.
- User-specific case constraints must be stored separately from generic instrument profiles.
