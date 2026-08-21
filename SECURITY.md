# Security Policy

## Reporting
Do not put private Matter data, credentials, privileged material, or exploit details in a public issue. Use the Foundation's designated private security-reporting channel once configured for the repository.

## Security invariants
- Authorization precedes retrieval/context construction.
- Retrieved content is untrusted data and cannot grant authority or tools.
- No repository may include private Matter records in source, fixtures, logs, history, screenshots, or examples.
- Secrets and production endpoints are prohibited from repository history.
- Security-sensitive changes require explicit tests and review.

This scaffold does not claim the repository has completed production security review.
