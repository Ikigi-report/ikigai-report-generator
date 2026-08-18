# Ikigai Report Generator

An authenticated web application for generating private, birth-data-first Ikigai calculation reports. It produces personal and two-person compatibility reports, stores report artifacts per account, supports English and Arabic display output, and allows secure Markdown, JSON, and PDF downloads.

> **Evidence boundary:** The application keeps deterministic symbolic calculations separate from recipient-supplied measurements. It does not invent assessment results or present relationship, health, hiring, or future-outcome claims as facts.

## Features

| Area | Included capability |
|---|---|
| Personal reports | Validated birth-data intake, optional Arabic name, optional **Group A — Supplied Measurements**, Markdown, JSON, and on-demand PDF export |
| Compatibility reports | Two-person intake, individual consent plus comparison consent, transparent calculated-overlap comparison, private artifact storage |
| Languages | English output and server-translated Arabic output with right-to-left rendering |
| Privacy | Manus OAuth authentication, user-scoped report history, signed artifact downloads, S3-backed report files |
| Safety | Explicit calculated-versus-supplied labels and method limitations in the generated report |

## Technology

The application uses **React 19**, **Vite**, **Tailwind CSS**, **Express**, **tRPC**, **Drizzle ORM**, and **MySQL/TiDB**. The report engine runs a bundled Python report kit (`report-kit/`) through a server-side Node.js child process. Generated Markdown and calculation JSON are saved in S3-compatible storage; PDFs are created on demand from stored Markdown.

## Prerequisites

Install the following for a local, self-hosted environment.

| Requirement | Purpose |
|---|---|
| Node.js 22+ and Corepack | Runs the React/Express application and `pnpm` |
| Python 3.11+ | Runs the report-kit calculation scripts |
| MySQL 8+ or compatible TiDB | Stores users and report metadata |
| Chromium and Pandoc | Renders PDF exports |
| S3-compatible object storage | Stores Markdown, JSON, and PDF artifacts |

The included `Dockerfile` installs Python, Chromium, Pandoc, DejaVu fonts, and Noto fonts for Arabic-capable production PDF rendering.

## Installation

### 1. Clone and install dependencies

```bash
git clone https://github.com/example-org/ikigai-report-generator.git
cd ikigai-report-generator
corepack enable
pnpm install
python3 -m pip install -r report-kit/requirements.txt
```

### 2. Configure environment variables

Create a local environment file or configure your deployment provider with the variables below. Do not commit secrets.

| Variable | Required | Purpose |
|---|---:|---|
| `DATABASE_URL` | Yes | MySQL/TiDB connection string |
| `JWT_SECRET` | Yes | Session-cookie signing secret |
| `VITE_APP_ID` | Yes | Manus OAuth application identifier |
| `OAUTH_SERVER_URL` | Yes | OAuth backend URL |
| `OWNER_OPEN_ID` | Yes | Project owner identifier used for administration |
| `BUILT_IN_FORGE_API_URL` | Arabic only | Server-side built-in AI endpoint used to translate Markdown |
| `BUILT_IN_FORGE_API_KEY` | Arabic only | Server-side built-in AI credential |
| Storage variables | Yes | Values required by the S3 storage helper in `server/storage.ts` |
| `BROWSER_BIN` | Production | Chromium path; defaults to `/usr/bin/chromium` in Docker |

The managed Manus deployment injects the OAuth, storage, and built-in AI variables automatically. For an external deployment, configure equivalent services before enabling sign-in, file storage, or Arabic translation.

### 3. Create the database schema

Generate and review the migration before applying it.

```bash
pnpm drizzle-kit generate
# Review the generated SQL under drizzle/
pnpm drizzle-kit migrate
```

The current schema includes `users` and `reports`. The `reports` table stores report metadata only; content bytes belong in object storage.

### 4. Start the application

```bash
pnpm dev
```

The development server listens on the port selected by the runtime. Do not hard-code a port in application code.

## Development commands

| Command | Use |
|---|---|
| `pnpm dev` | Start the Vite/Express development server |
| `pnpm check` | Run TypeScript validation |
| `pnpm test` | Run Vitest tests |
| `pnpm build` | Build the client and server bundles |
| `pnpm start` | Run the production Node bundle |
| `pnpm format` | Format project files with Prettier |

## Report generation flow

1. The authenticated user completes a validated intake form.
2. The server validates Latin name, ISO date, 24-hour time, place, language, and any supplied measurements.
3. The server invokes `report-kit/scripts/generate_report.py` through a child process.
4. The server saves Markdown and calculation JSON under a user-and-report-specific storage prefix.
5. The metadata row stores only the artifact keys, selected language, report type, and display fields.
6. The viewer reads the report after an owner-scoped database lookup.
7. PDF export converts stored Markdown on demand, stores the resulting PDF, and returns a signed download URL.

## Personal-report input policy

The personal intake requires a Latin-script name, birth date, local birth time, and birth place. An Arabic name is optional and is used only where the calculation engine supports it.

**Group A — Supplied Measurements** is optional. Each selected measurement must contain a real user-provided result and a confirmation that it came from a completed assessment. Do not calculate, infer, score, or auto-fill psychometric results from birth data.

## Compatibility reports

Compatibility reports are stored as a report type of `compatibility` with a primary and secondary recipient name. The application requires consent for each person and separate consent for the comparison.

The compatibility markdown compares only values that are actually present in the two calculation JSON records. It labels the headline percentage as a **symbolic alignment index**, explains the comparable outputs, and includes a method boundary. It is not a scientific measurement or a decision tool for relationship, marriage, hiring, health, or future outcomes.

## Arabic output

The server first generates the canonical report, then translates display Markdown on the server. Arabic output is wrapped with right-to-left direction and rendered with Arabic-capable fonts. Calculations JSON remains canonical so it can be audited independently of display-language translation.

Before changing the translation model, retrieve the live model catalog and keep the request server-side. Preserve names, numbers, dates, percentages, URLs, calculation labels, tables, and evidence-boundary statements in translation prompts.

## PDF download and email delivery

Compatibility reports have an explicit **Prepare/Download compatibility PDF** action in the report viewer and history. Export uses the same protected user-scoped route as personal reports.

The interface includes an **Email PDF** placeholder. Real delivery is intentionally disabled until a transactional provider is configured. To enable it, add a verified Resend sender address and `RESEND_API_KEY` through the project secrets interface, then implement recipient validation, owner-scoped report lookup, PDF attachment sending, audit logging, and error handling. Do not use a personal Gmail or Outlook connection as the production email backend.

## Deployment

### Managed Manus deployment

Save a checkpoint to publish the current version. The managed environment supplies the OAuth, storage, database, and built-in AI credentials configured for the project.

### Docker deployment

The `Dockerfile` builds the report kit and the Node application in one image. Ensure that your container runtime provides:

- a production database connection;
- persistent S3-compatible storage;
- OAuth configuration matching the published URL;
- a writable temporary directory for report generation; and
- enough request time for Python calculation and PDF generation.

Do not rely on local filesystem artifacts after a request completes.

## Security and privacy

- Protect every report procedure with authentication.
- Query report records by both report ID and authenticated user ID before reading or returning artifact links.
- Store files in object storage and metadata in the database.
- Use opaque, per-report storage prefixes rather than user-provided filenames.
- Keep built-in AI and any transactional-email keys server-side.
- Request fresh confirmation before generating persistent test records in a real user account.

## Testing checklist

Run this baseline before releasing a change.

```bash
pnpm check
pnpm test
pnpm build
```

Also verify a real authenticated personal-report flow, a compatibility-report flow, Arabic right-to-left rendering, Markdown/JSON/PDF downloads, and responsive report viewing. Test email delivery only after a verified transactional sender is configured.

## Repository and project links

- GitHub: https://github.com/example-org/ikigai-report-generator
- Published app: https://example.invalid

## License

This project is licensed under the MIT License. Review the licenses and terms for the bundled report kit and any third-party services before commercial distribution.
