# Rust implementation decision

## Decision

Keep the current **TypeScript/React/Express** application and the **Python** report-kit runtime. Do not rewrite the primary application in Rust at this stage.

## Reasoning

The product already depends on React UI components, tRPC contracts, Manus OAuth, Drizzle/MySQL access, managed storage helpers, and a Python calculation engine. Replacing these layers with Rust would add a second service boundary, duplicate authentication and storage work, complicate deployment, and delay contributor onboarding without improving the current report-generation bottleneck.

Rust is a good future option only for a measured hotspot, such as deterministic bulk calculation, complex document conversion, or a standalone CLI that proves materially faster or safer than the existing implementation. Any Rust addition should be isolated behind a stable command or API contract, benchmarked against the current implementation, and introduced with tests and reproducible builds.

## Contribution guidance

Prefer TypeScript for web and server features and Python for report-kit logic. Propose Rust only with a clear problem statement, baseline measurement, interface design, deployment plan, and maintenance owner.
