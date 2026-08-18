# Public release checklist

Before changing repository visibility, verify the following.

- [ ] No credentials, environment files, user reports, generated PDFs, database files, or storage URLs are tracked.
- [ ] No personal names, email addresses, location details, account IDs, project domains, or private repository URLs remain in current files.
- [ ] Git history has been inspected and, if needed, rewritten before public release.
- [ ] Repository ownership does not reveal a personal identity when that is not desired.
- [ ] `LICENSE`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, and `SECURITY.md` are present.
- [ ] Issue and pull-request templates are present.
- [ ] `pnpm check` and `pnpm test` pass.
- [ ] The project is made public only after a maintainer reviews the final diff and repository settings.
