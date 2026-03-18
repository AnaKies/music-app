# Architecture Index

This directory contains the approved target architecture for the project.

## Documents

- [Architect Agent](../../agents/Architect.md): Behavior definition of the project-specific architecture agent.
- [Architecture Overview](./overview.md): High-level architecture for the AI-guided sheet music transposition system.
- [System Context](./system-context.md): User flow, system boundaries, and top-level component relationships.
- [Module Design](./module-design.md): Internal services, ownership boundaries, and runtime responsibilities.
- [Interfaces](./interfaces.md): External APIs and internal contracts between major components.
- [Data Model](./data-model.md): Core entities, lifecycle expectations, and persistence direction.
- [Observability](./observability.md): Runtime status, warnings, recommendation traceability, and processing metadata.
- [Frontend State Mapping](./frontend-state-mapping.md): UI-facing case states, async states, and frontend interpretation of backend flow.
- [Architecture Features](./features.md): Small MVP-first feature slices and their responsible agents.
- [Repository Structure](./repository-structure.md): Recommended repository layout for implementation boundaries and junior-friendly work allocation.

## Structure Rules

- New architecture topics should be documented in dedicated files.
- Existing topic files should be extended when the discussion goes deeper into the same topic.
- Large topics should be split into subtopics and linked from this index.

## Navigation

This file is the primary navigation entry for architecture documentation in Obsidian.
