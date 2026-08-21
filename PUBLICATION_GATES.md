# Publication Gates

## Repository status

`planned-prepublication`

## Reconciliation gate

Before public release:
1. identify controlling canonical requirements;
2. live-inspect and pin every candidate upstream used;
3. compare the public scaffold with stronger implementations;
4. classify intentional omissions;
5. document public/private boundary;
6. resolve source provenance and rights;
7. define and pass relevant conformance profiles.

## Repository-specific gates

- One documented startup path
- No production endpoints/secrets
- Pinned versions
- Successful macOS dev + Linux CI smoke test

## Common release gates

- architecture/current-state truthfulness;
- implementation vertical slice;
- privacy/worktree hygiene;
- full-history secret/security scan;
- rights/license/provenance review;
- contributor documentation;
- remote CI/security controls;
- explicit human publication acknowledgement.
