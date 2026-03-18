# Frontend Application Structure

Reference: [Frontend Index](./index.md)
Related architecture: [Module Design](../architecture/module-design.md)
Related interfaces: [Interfaces](../architecture/interfaces.md)
Related frontend state mapping: [Frontend State Mapping](../architecture/frontend-state-mapping.md)

## Purpose

This document defines the planned page, feature, and state structure of the MVP frontend.

## Planned Feature Areas

- `cases`: case listing, default-entry selection, create, switch, and reset interactions
- `interview`: question rendering, answer submission, validation, progress state
- `upload`: file selection, upload handling, parsing feedback
- `recommendations`: recommendation list, stale-state handling, warnings, selection
- `transformation`: job polling, progress state, retry handling
- `results`: download action, optional print handoff, warning summary
- `shared`: reusable UI primitives, layout, API client helpers, validation utilities

## Planned Shared UI Families

- `workspace-shell`: the consistent stage frame used across interview, upload, recommendation, transformation, and result screens
- `stage-header`: title, progress framing, and local status summary
- `status-strip`: compact status, warning, confidence, and failure communication near the active work area
- `recommendation-card`: primary and secondary recommendation presentation with selection affordance
- `action-panel`: the main decision or submission zone within a stage
- `context-panel`: secondary contextual information such as case summary or warning explanation

## Planned Directory Shape

```text
src/
  app/
  features/
    cases/
    interview/
    upload/
    recommendations/
    transformation/
    results/
  components/
    workspace/
    status/
    recommendations/
    actions/
  lib/
    api/
    validation/
    utils/
  styles/
```

## Frontend Structure Diagram

```mermaid
flowchart TD
    APP[App Router Screens]
    APP --> CASES[Cases Feature]
    APP --> INTERVIEW[Interview Feature]
    APP --> UPLOAD[Upload Feature]
    APP --> REC[Recommendations Feature]
    APP --> TX[Transformation Feature]
    APP --> RESULT[Results Feature]

    CASES --> API[Frontend API Client]
    INTERVIEW --> API
    INTERVIEW --> VALID[Validation Layer]
    UPLOAD --> API
    REC --> API
    TX --> API
    RESULT --> API

    APP --> SHARED[Shared Components]
    APP --> TOKENS[Styles and Tokens]
```

Diagram purpose:
Show the planned frontend feature decomposition and the shared layers that support page-level implementation.

What to read from it:
The UI is organized by product feature, while API access, validation, and reusable components stay centralized in shared support layers. The shared component layer should explicitly support the repeated workspace, status, and recommendation patterns defined by design.

Why it belongs here:
This file owns the internal frontend structure and the implementation shape of the UI layer.

## State Handling Plan

- Local component state should handle transient view behavior such as modal visibility or local selection.
- `react-hook-form` should own interview-form state and validation lifecycle.
- `TanStack Query` should own backend-derived state such as cases, recommendations, transformations, and polling.
- Long-running upload and processing states should be read from dedicated status queries such as `GET /cases/{id}`, `GET /scores/{id}`, and `GET /transformations/{id}` instead of being inferred from mutation success alone.
- Recommendation freshness must be derived from case-constraint changes and surfaced as explicit UI state.
- Global state should be introduced only if cross-feature coordination becomes unmanageable with local state and query caches.
- Environment-specific API configuration should stay in one frontend infrastructure boundary rather than leaking per-feature endpoint assumptions across the codebase.

## Screen Responsibilities

- Case entry screen: show the default suggested case, other reusable cases, and case-creation entry
- Interview screen: render question objects and submit structured answers
- Upload screen: block upload until the selected case is ready and show parsing status
- Upload screen: poll score-status snapshots after upload acceptance until parsing and recommendation readiness become visible
- Recommendation screen: show primary and secondary recommendations, warnings, and stale state
- Transformation screen: show progress, retry path, and failure messaging
- Result screen: expose MusicXML download and optional print handoff

## Design Alignment Notes

- The frontend should implement a repeated workspace-shell pattern instead of inventing a different layout composition for each stage.
- Recommendation cards should exist as a dedicated component family because they are the most product-specific interaction element in the MVP.
- Status chips, warning callouts, and confidence markers should share one visual logic so queued, processing, low-confidence, failure, and completion states do not drift between screens.

## Safety Alignment Notes

- Retry actions should be rendered only when backend status metadata explicitly marks the path as retryable.
- User-facing status areas should prefer `safeSummary` and typed severity metadata instead of raw technical diagnostics.
- The frontend should not render raw upload contents, raw provider output, internal storage paths, or backend exception text as normal workflow UI.
- Low-confidence recommendations must remain visually distinct from normal success or completion states.

## Testing Priorities

- verify case entry and case switching behavior
- verify interview question rendering for multiple question types
- verify upload gating based on case readiness
- verify `queued`, `parsing`, recommendation-ready, and failed states render from typed backend snapshots rather than mutation assumptions
- verify stale recommendation behavior after case edits
- verify transformation polling and result-state transitions
- verify retry actions appear only for retryable backend states
- verify low-confidence and blocked-confidence recommendation states stay visually and behaviorally distinct
- verify raw technical diagnostics are not surfaced as normal user-facing workflow content
