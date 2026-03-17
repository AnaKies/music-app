# Architecture Overview

Reference: [Architecture Index](./index.md)

## Purpose

This document summarizes the approved high-level architecture direction for the AI-guided sheet music transposition system.

## Current Scope

This overview defines the architectural baseline for:

- system structure
- module boundaries
- interfaces
- data model
- non-functional architecture constraints

## Documentation Principle

Only approved final architecture belongs here.
Working notes, negotiation history, and discarded alternatives are intentionally excluded.

## Approved Architecture Direction

The approved target direction is an AI-guided decision architecture with deterministic execution.
AI is responsible for structured user interviewing, instrument-specific capability interpretation, and recommendation of target transposition ranges.
Backend logic is responsible for validated score parsing, deterministic transposition, export, and persistence.

## Architectural Principles

- AI supports decision-making, but deterministic backend logic owns final score mutation
- user-specific constraints persist inside a reusable transposition case
- uploaded score formats are isolated from internal domain logic through a canonical score model
- recommendation and execution are separate responsibilities
- original and transformed artifacts remain separately stored and traceable

## Product Scope Direction

The initial product scope is a focused transposition system, not a full composition platform.
The architecture still preserves a growth path toward a larger sheet-processing platform.

## Document Role

This file explains the overall architectural direction and governing principles.
Detailed actor flow, system boundaries, and runtime interactions belong in [System Context](./system-context.md).

## Non-Functional Priorities

- maintainability through clear module boundaries
- reliability through immutable original-file storage
- extensibility through a canonical score model
- safety through strict input validation and constrained AI decision boundaries
- observability through interview state, recommendation outputs, job status, and processing metadata

## Maintenance Rule

The architecture agent maintains this documentation in parallel with architecture discussions after explicit user approval.
