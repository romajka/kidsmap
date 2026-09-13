# KidsMap Account Data Retention Policy

> **Status: DRAFT — NOT APPROVED — SELF-SERVICE DELETION MUST REMAIN DISABLED**

This document is the activation record for account deletion. Replace every bracketed value, obtain a written decision from the authorized privacy/legal and infrastructure owners, then configure the same immutable values in `ACCOUNT_DELETION_RETENTION_POLICY_JSON`.

**Policy version:** `[ADRP-YYYY-NN]`
**Effective date:** `[YYYY-MM-DD]`
**Approved by:** `[role, person or decision record]`
**Grace period:** `[N calendar days]`
**Processor cadence:** `[daily UTC time and operational owner]`

| Data category | Disposition | Retention | Legal basis / owner |
| --- | --- | --- | --- |
| Account identifiers and profile | delete | `[duration after confirmed request]` | `[approved basis and owner]` |
| Favorites, reactions, cooldowns, sessions and active invitations | delete | `[confirmation or completion date]` | `[approved basis and owner]` |
| Published place/site/specialist reviews | `[delete, or anonymize by removing account link and author name]` | `[duration]` | `[approved basis and owner]` |
| Pending or rejected reviews | `[delete or another approved disposition]` | `[duration]` | `[approved basis and owner]` |
| Moderation and ownership history | `[redact/anonymize]` | `[duration]` | `[approved basis and owner]` |
| Published Place, Event and Specialist content | `[unlink owner, transfer, or delete]` | `[duration]` | `[approved handover rule and owner]` |
| Draft owner content | `[delete, transfer, or retain]` | `[duration]` | `[approved handover rule and owner]` |
| Security/deletion audit | retain pseudonymously | `[duration]` | `[approved basis and owner]` |
| Product analytics | `[delete linked events / aggregate only]` | `[duration]` | `[approved basis and owner]` |
| Legal hold | defer processor without restoring login | `[release authority and review interval]` | `[approved authority]` |
| Backups | expire; never mutate historical backups in place | `[maximum expiry across every destination]` | `[infrastructure/backup owner]` |

## Required user-facing copy

Approve exact text in Azerbaijani, Russian and English for every key below. These values are supplied in the policy JSON and displayed by the application; they are not hard-coded as legal promises.

| Key | AZ | RU | EN |
| --- | --- | --- | --- |
| `deleted` | `[text]` | `[text]` | `[text]` |
| `anonymized` | `[text]` | `[text]` | `[text]` |
| `legal_hold` | `[text]` | `[text]` | `[text]` |
| `owner_content` | `[text]` | `[text]` | `[text]` |
| `backups` | `[text]` | `[text]` | `[text]` |

## Supported first-release dispositions

The current processor accepts only these reviewed technical modes:

- `review_disposition`: `anonymize_approved_delete_other` or `delete_all`;
- `owner_content_disposition`: `unlink_public_delete_team_access`;
- `moderation_history_disposition`: `anonymize`;
- `analytics_disposition`: `delete_user_events`.

A different policy decision requires a separate implementation review before activation.

## Backup inventory checkpoint

The repository backup script currently keeps at most five local files and removes files older than 15 days. This is only repository evidence. The infrastructure owner must inventory immutable, off-site, provider and manually copied backups and approve the maximum expiry that appears in user-facing copy.

## Activation checklist

- [ ] Every bracketed value above is replaced.
- [ ] Privacy/legal owner approval is linked.
- [ ] Infrastructure owner confirms every backup destination and expiry.
- [ ] AZ/RU/EN copy is approved.
- [ ] The production scheduler, timeout and failure alert are assigned.
- [ ] The exact approved object is configured with `"active": true`.
- [ ] A dry run is reviewed before the first production processing run.
