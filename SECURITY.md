# Security Policy

## Supported versions

GradPath AI is pre-release software. Only the latest `main` branch receives
security fixes.

## Reporting a vulnerability

Do not open a public issue containing vulnerability details, credentials, CVs,
or personal information. Use GitHub's private vulnerability-reporting feature
for this repository when available.

Include:

- the affected component and commit;
- reproducible steps using synthetic data;
- expected and observed behaviour;
- potential confidentiality, integrity, or availability impact;
- any safe mitigation you have identified.

## Sensitive-data rules

- Use only synthetic or properly redacted data in development and tests.
- Never commit `.env`, tokens, keys, real CVs, or exported candidate documents.
- Treat uploaded document content and model output as untrusted input.
- Do not include document contents or personal data in logs or issue reports.

