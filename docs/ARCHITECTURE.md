# Architecture

## Boundary

Reproducible synthetic local environment for contributing across the NORA OSS ecosystem without private infrastructure or Matter data.

This repository owns only its public contract and implementation boundary. Canonical private Matter/application state remains in NORA One Core.

## Dependency direction

- Released artifacts/images/packages from public repos only

## Design invariants

- Public interfaces are versioned and independently testable.
- No implicit import of private NORA One source trees.
- Provider-specific behavior stays behind adapters.
- Structured outputs carry enough provenance/version information for review.
- Failure/unknown states are explicit rather than converted into confident prose.

## Integration rule

NORA One consumes this repository through released packages, typed APIs, or explicit protocols. Reference repositories are adoption sources, not mutable production dependencies.
