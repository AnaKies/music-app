# Module Design

Reference: [Architecture Index](./index.md)

## Design Principle

The system uses an AI-guided decision architecture with deterministic transposition.
AI gathers structured musical constraints from the user and recommends one or more suitable target ranges.
The backend applies the user-selected target range through deterministic score-processing logic.

## Core Modules

### Frontend

Purpose:
Collect questionnaire input, upload score files, present AI recommendations, and present processing results.

Responsibilities:

- run the AI-guided questionnaire flow
- upload MusicXML files
- display recommended target ranges
- collect the user-selected recommendation
- show job progress and warnings
- provide result download

### Backend API

Purpose:
Provide the public application interface for questionnaire state, uploads, recommendation retrieval, transformation requests, and result retrieval.

Responsibilities:

- request validation
- job creation
- recommendation persistence access
- persistence coordination
- status reporting
- result delivery

### AI Interview Service

Purpose:
Conduct an adaptive questionnaire that identifies the relevant instrument and playable constraints.

Responsibilities:

- ask follow-up questions based on prior user answers
- infer or confirm instrument identity
- collect highest and lowest playable tones
- collect unplayable tones or problematic registers
- collect difficult or unwanted tonalities
- produce a structured player constraint profile

### Score Parser

Purpose:
Convert MusicXML into the canonical internal score representation.

Responsibilities:

- parse score structure
- normalize notes, measures, parts, clefs, and signatures
- surface parse and validation errors

### Canonical Score Model

Purpose:
Serve as the internal contract between parser, recommendation analysis, transformation engine, and exporter.

Responsibilities:

- normalize musical structure
- isolate domain logic from source file format details
- support versioned evolution of transformation logic

### Instrument Knowledge Service

Purpose:
Provide structured knowledge about each instrument and its practical musical constraints.

Responsibilities:

- store instrument profiles
- expose absolute written and sounding ranges
- expose comfortable playing ranges
- expose transposition metadata
- expose difficult or unsuitable key signatures
- expose notation preferences where needed

### AI Recommendation Service

Purpose:
Recommend one or more suitable target ranges for the uploaded score.

Responsibilities:

- analyze the uploaded score against the player constraint profile
- evaluate instrument limits and comfortable ranges
- evaluate key suitability for the target instrument
- propose one or more target ranges instead of assuming a single answer
- provide recommendation explanations and confidence metadata

### Transformation Engine

Purpose:
Execute deterministic transposition after the user selects a recommended range.

Responsibilities:

- transpose notes into the selected target range
- enforce configured range constraints
- preserve musical structure where possible
- emit warnings when exact adaptation is not cleanly possible

### Export Service

Purpose:
Convert the transformed canonical score back into a supported output format.

Responsibilities:

- generate MusicXML output
- validate export consistency
- store generated artifacts

### Storage Layer

Purpose:
Persist documents and metadata separately according to access pattern.

Responsibilities:

- object storage for original and transformed files
- metadata store for jobs, requests, warnings, and document references

## Ownership Boundaries

- Frontend owns user interaction only.
- Backend API owns external request contracts.
- AI interview and recommendation services own conversational and recommendation behavior.
- Structured instrument knowledge must remain available outside the model and must not exist only as prompt memory.
- Deterministic score conversion belongs to parser and transformation engine.
- AI services must remain replaceable and must not define the canonical data model.
- Export logic must depend on the canonical score model, not directly on the upload format parser.
