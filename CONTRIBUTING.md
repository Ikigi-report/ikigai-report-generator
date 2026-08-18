# Contributing

Thank you for helping improve Ikigai Report Generator. Contributions should preserve the project’s privacy, evidence-boundary, and consent requirements.

## Before opening an issue

Search existing issues first. For bugs, include the route, expected behavior, observed behavior, browser or runtime details, and a minimal reproduction that contains no real birth data, report content, credentials, or account information.

## Development workflow

1. Fork the repository and create a focused branch from `main`.
2. Install dependencies with `pnpm install` and the report-kit dependencies described in the README.
3. Add or update tests when changing validation, report storage, access control, calculation logic, or exports.
4. Run `pnpm check` and `pnpm test` before opening a pull request.
5. Describe user-facing behavior, evidence-boundary impact, and any migration or secret requirement in the pull request.

## Contribution rules

Do not commit real names, dates of birth, times, places, user reports, API keys, OAuth credentials, screenshots with account details, or production database exports. Use clearly fictitious examples such as `Casey Example` and `Sample City, Example Country`.

Do not add logic that invents psychometric scores, turns symbolic calculation into diagnosis or prediction, or makes high-stakes relationship, medical, employment, financial, or legal claims. Group A inputs must remain recipient-supplied and explicitly confirmed.

## Pull request expectations

Keep pull requests focused and explain trade-offs. Add migrations for schema changes, keep stored files out of database columns, and enforce owner-scoped access for every report read, download, export, or delivery action.
