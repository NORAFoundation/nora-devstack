# Contributing

This repository is structured for bounded, reviewable contributions.

## Before coding
1. Read `CHARTER.md` and `docs/ARCHITECTURE.md`.
2. Check `UPSTREAM_SOURCES.yaml` before implementing a capability that may already exist elsewhere in the NORA estate.
3. Do not copy code from an upstream candidate until the exact source/ref and rights status are recorded.
4. Add or update tests for behavior changes.
5. Keep synthetic fixtures synthetic.

## Pull requests
A PR should state the objective, affected contract, security/privacy/evidence implications, tests, compatibility/migration effects, and whether the change alters a public API.

## Maturity language
Use: Principle -> Requirement -> Implemented -> Verified -> Deployed -> Validated -> Certified. Do not upgrade a claim without evidence.
