# Repository Charter — `nora-devstack`

**Portfolio wave:** D  
**Scaffold status:** `planned-prepublication`

## Exact purpose

Reproducible synthetic local environment for contributing across the NORA OSS ecosystem without private infrastructure or Matter data.

## Public API / contract

nora-dev up/down/reset/seed/doctor/test/logs; devstack.yaml and locked service/image manifest.

## Packages / modules

- compose
- scripts
- seed
- observability
- fixtures
- docs

## Non-goals

- Production Terraform
- Production credentials
- Hosted topology mirror
- Private corpora
- Production performance benchmark

## Upstream source candidates

- NORAFoundation/nora-aapl@706494bf4ca4011027c365e38dccc8d747535030
- Platform/deployer scaffolds: reconcile before adoption

Every source candidate is a reconciliation input, not automatically an adoption source. Unpinned candidates must be live-inspected before any code migration.

## Dependency direction

- Released artifacts/images/packages from public repos only

## Contribution areas

- Containers
- Deterministic setup
- Fixture seeding
- Health checks
- Local observability
- Contributor onboarding

## Required tests

- Clean startup
- Pinned versions
- Health checks
- Migration
- Seed idempotency
- No production endpoints
- Synthetic-only data

## Publication gate

- One documented startup path
- No production endpoints/secrets
- Pinned versions
- Successful macOS dev + Linux CI smoke test

## NORA One integration

Engineering uses the same public modules in private integration environments; devstack is not production deployment source of truth.

## Maturity boundary

This scaffold establishes repository shape and interface intent. It does not by itself prove implementation completeness, public-release readiness, deployment, validation, or certification.
