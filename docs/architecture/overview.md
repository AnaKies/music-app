# Architecture Overview

Reference: [Architecture Index](./index.md)

## Purpose

This directory stores the approved final-state software architecture for the AI-based music sheet octave converter.

## Current Scope

The architecture documentation maintained here may cover:

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

The initial product scope is a focused converter, not a full composition platform.
The architecture still preserves a growth path toward a larger sheet-processing platform.

## Non-Functional Priorities

- maintainability through clear module boundaries
- reliability through immutable original-file storage
- extensibility through a canonical score model
- safety through strict input validation and constrained AI decision boundaries
- observability through interview state, recommendation outputs, job status, and processing metadata

## Maintenance Rule

The architecture agent maintains this documentation in parallel with architecture discussions after explicit user approval.
