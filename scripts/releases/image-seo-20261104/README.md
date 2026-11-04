# Image SEO release — 2026-11-04

User-authorized production correction. The application source overlay was built from the running production image, not from the dirty local checkout.

- Base image: `kidsmap:release-20261102-945db451455e`.
- Base revision: `945db451455eac97a86fe82ecc3ab5e065bf2b9a`.
- Release image: `kidsmap:image-seo-20261104-0e1f97c347e5`.
- `source.patch`: the exact 13-file application diff against that deployed baseline.
- `manifest.json`: SHA-256 before/after for every changed file.
- `activate.py`: actual server activation procedure; validates baseline, preserves service settings, checks unapplied migrations without applying them, collects static without clearing, and rolls back on activation/verification failure.
- Production rollback/configuration artifacts remain only in `/opt/kidsmap-releases/20261104-image-seo` (mode 0700). They contain environment configuration and must never be copied into the repository.
- Local tests and rendered evidence: `.tmp/image-seo-release-20261104/`; screenshots: `output/playwright/image-seo-release-20261104/`.

Do not rerun this activation against an already upgraded image or replay the whole working tree. A later release must include the equivalent source changes and revalidate its actual baseline. The local unpublished parks guide and unrelated UI work were excluded. No database records or migrations changed. No Git commit/push was requested or performed.
