# PLACE-QA-01 — Rejection feedback implementation plan

> **For agentic workers:** Execute task-by-task only after the user approves this scope. Use the available `test-driven-development` and `verification-before-completion` skills. Execution is sequential in this chat; no commit/push/deploy. The writing-plans generic commit/subagent suggestions are overridden by the user's bounded task.

**Goal:** Владелец видит последнюю сохранённую причину отказа в continuous-редакторе места после reload, нового входа и сохранения исправлений.

**Architecture:** Использовать существующий `place_revision.review_note`, полученный после действующей проверки доступа. Шаблон показывает текст при `rejected`, `declined` и при сохранённом `draft`; действующий `publication.propose(submit=True)` очищает причину при повторной отправке. Подпись входит в существующий `form.wizard_copy`, CSS ограничен новым блоком.

**Tech Stack:** Django 6.0.2 / Python 3.12.15, Django templates, существующие CSS, PostgreSQL QA, Chromium.

**Spec:** [PLACE-QA-01](../../qa/module01-2026-10-09-r2/findings/PLACE-QA-01.md). [Текущий аудит scope](../../qa/place-qa01-plan-2026-10-10/REPORT.md).

## Authorization and snapshot

- Status: PLAN / AWAITING USER SCOPE APPROVAL. Implementation has NOT started.
- Checkout `C:\kidsmap`; branch `task33-progress`; HEAD `8d188b316f800fbedf0b1e376905dfd4924cb1b6`; `docs/task33/implementation-status.md` reports `active_run: NONE`.
- Entry changes: modified `docs/qa/module-acceptance-prompts.md`; untracked directories `module01-2026-10-09-r1`, `module01-2026-10-09-r2`, `module02-2026-10-09-r1`, `module03-2026-10-10-r1` under `docs/qa`. Preserve them and all existing stands.
- Source confirms the missing rendering. The historical browser failure has NOT been repeated in this planning phase. Fresh runtime reproduction is Task 1 before any application edit.

## Global constraints

- Only PLACE-QA-01. Preserve ACL, revision lifecycle, publication rules and other screens.
- No production credentials, external integrations, commit, push or deploy. No application or database cleanup.
- Tests require `DJANGO_TESTING=1`; dedicated DB/test DB, cache, media, private-media, email and browser profile. No inherited `.env` or existing stand data.
- Use synthetic actors/content only. Store passwords/cookies/raw sensitive HTML in ignored scratch, never in report artifacts.
- `review_note` is moderator-provided text: autoescape stays enabled; no `safe`, no HTML interpretation, no truncation. Preserve newlines and wrap long strings.
- No model/migration/ACL/controller/publication service changes. If fresh reproduction requires those changes, return with the concrete discrepancy before expanding scope.

## Source and behavior contract

1. `src/catalog/models/volunteer.py:15` uses a OneToOne relation to Place. There is one current revision, not a history requiring “latest” sorting.
2. `src/catalog/views.py:1384` passes the revision; `owner_place_edit` obtains the editable place through the controller before rendering both GET and invalid POST.
3. `src/catalog/services/publication.py:408` stores the stripped moderation reason. At line 360, draft save preserves it and submit clears it.
4. `src/catalog/templates/pages/includes/owner_place_continuous.html:7` displays lifecycle without review text. `owner_place_edit.html` extends `permanent_place_form.html`, which includes this continuous template.
5. `src/catalog/services/permanent_place_wizard.py:ui_copy` supplies RU/AZ/EN copy through the existing `copy(ru, az, en)` helper. New labels need no `.po/.mo` regeneration.

| Current revision | Reason | Expected block |
|---|---|---|
| rejected / declined | nonempty | Show saved reason |
| draft after correction | nonempty preserved reason | Show latest reason |
| any | empty | No empty block |
| pending / approved | any, including defensive stale fixture | Hidden |
| absent / new place | absent | Hidden |

The text is not translated; the heading is localized. After resubmit the existing service clears the field; this plan does not introduce an audit-history feature.

## File ownership and allowed diff

One sequential executor, frontend-reviewer scope with publication/ACL checks; no claim of independent review.

| File | Proposed change |
|---|---|
| `src/catalog/templates/pages/includes/owner_place_continuous.html` | Conditional reason block immediately after lifecycle and before form |
| `src/catalog/services/permanent_place_wizard.py` | One `review_note_title` key in `ui_copy` |
| `static/css/pages/owner_place_continuous.css` | New block only: spacing, preserved line breaks, long-text wrapping |
| `src/catalog/templates/pages/permanent_place_form.html` | Bump only continuous stylesheet cache version |
| `src/catalog/testcases/test_place_rejection_feedback.py` (new) | Regression tests for rendered content, persistence, locales, escaping and access |
| `docs/qa/place-qa01-fix-2026-10-10/` (new) | QA launcher/settings, report, sanitized evidence, commands and screenshots |
| `.tmp/place-qa01-fix-20261010/` (ignored, new) | Isolated fixtures/media/private-media, credentials and raw diagnostics |

Historical findings/reports and the shared implementation journal are preserved; new run ownership is recorded in the new report. Recheck `active_run` before starting execution.

## Task 1: Fresh isolated reproduction and RED regression

- [ ] Recheck HEAD, dirty status, active_run and occupied ports. Hash incoming dirty files and relevant application sources; preserve rather than copy private scratch content. If another run appears, coordinate ownership before touching shared sources.
- [ ] Provision a new disposable PostgreSQL stand on loopback port 55435 and HTTP on 8815 if still free. Docker is callable through `wsl.exe --exec docker`; server availability was checked during planning. Example exact provision command, run only during execution:

```powershell
wsl.exe --exec docker run -d --name placeqa01-20261010-pg --publish 127.0.0.1:55435:5432 --env POSTGRES_DB=placeqa01 --env POSTGRES_USER=placeqa01 --env POSTGRES_HOST_AUTH_METHOD=trust postgres:17
```

Use `placeqa01` and `test_placeqa01` only. Inspect only this container's readiness; do not stop/reconfigure existing containers. If the port/name is occupied, use a new unique run suffix and record the actual command.

- [ ] Create reviewed QA-only `run.py` / `qa_settings.py` under the new report directory, adapting the isolation pattern from `module01-2026-10-09-r2/run.py` and `qa_settings.py`. Clear inherited service credentials before settings import; assert testing, DB host/port/name, LocMem cache/mail and distinct media/private-media roots. Block external sockets and browser requests; declare blocked maps/CDN integrations in NOT RUN. Do not execute the historical launcher or reuse its database.
- [ ] Record every native command and exit code via a subprocess ledger. Create synthetic owner, outsider and moderator identities. Seed only identities/taxonomy; create and submit the investigated place through the real owner UI.
- [ ] Reproduce owner create/submit → moderator reject → editor → reload → logout/login on the new stand. Read back saved reason/status/version through restricted synthetic-fixture diagnostics. Save the before screenshot and measured failure.
- [ ] Add `test_place_rejection_feedback.py`, using existing `PublicationFixture` helpers. Core RED test:

```python
from django.test import TestCase
from django.urls import reverse
from django.utils.html import escape
from django.utils.translation import override
from catalog.testcases.test_task33_publication import PublicationFixture


class PlaceRejectionFeedbackTests(PublicationFixture, TestCase):
    def test_saved_reason_survives_reload_and_new_session(self):
        note = 'QA reason <script>window.qaUnexpected = 1</script>\nSecond line & detail'
        revision = self.propose({'description_az': 'QA revised description'})
        self.s.review(actor=self.staff, revision_id=revision.pk,
                      version=revision.version, approve=False, note=note)
        revision.refresh_from_db()
        self.assertEqual(revision.review_note, note)
        self.client.force_login(self.owner)
        with override('ru'):
            url = reverse('owner_place_edit', args=[self.place.pk])
            for attempt in range(3):
                if attempt == 2:
                    self.client.logout()
                    self.client.force_login(self.owner)
                response = self.client.get(url)
                self.assertContains(response, 'data-place-review-note')
                self.assertContains(response, escape(note))
                self.assertNotContains(response, '<script>window.qaUnexpected')
        revision.refresh_from_db()
        self.assertEqual(revision.review_note, note)
```

`force_login` validates session independence only; the browser gate separately uses real login/logout. Add the following explicit cases to this file:

- `final_reject=True` and ordinary rejection both show the stored text.
- RU/AZ/EN requests assert their exact heading and the identical saved reason.
- `propose(submit=False, revision_version=current.version)` after rejection preserves reason in DB and rendered editor; invalid form POST also displays it.
- `propose(submit=True, revision_version=current.version)` clears reason and hides the block; a subsequent second rejection displays the new text and not the old one.
- Empty reason, no revision and pending/approved fixtures with a stale note have no `data-place-review-note` block.
- Outsider and anonymous clients cannot retrieve the note via the owner endpoint; follow redirects and assert absence of the unique synthetic note.
- Multiline and long unbroken text remains complete; script/tag/ampersand input is escaped. Public place page has no unique synthetic reason.

```powershell
.venv/Scripts/python.exe docs/qa/place-qa01-fix-2026-10-10/run.py test catalog.testcases.test_place_rejection_feedback
```

Expected before implementation: reason-visibility assertions FAIL; distinguish unexpected environment/setup errors and do not change assertions to obtain green.

## Task 2: Minimal presentation change and GREEN regression

- [ ] Add this conditional block after the existing lifecycle element, retaining Django autoescape:

```django
{% if place_revision.review_note %}
  {% if place_revision.status == 'rejected' or place_revision.status == 'declined' or place_revision.status == 'draft' %}
    <aside class="pc-note pc-review-note" data-place-review-note aria-labelledby="pc-review-note-title">
      <strong id="pc-review-note-title">{{ ui.review_note_title }}</strong>
      <p class="pc-review-note-body">{{ place_revision.review_note }}</p>
    </aside>
  {% endif %}
{% endif %}
```

- [ ] Add the copy key to `ui_copy()`:

```python
review_note_title=t('Последняя причина отказа', 'Son imtinanın səbəbi', 'Latest rejection reason'),
```

- [ ] Add scoped styles and change the continuous CSS version to `20261010_place_qa01`:

```css
.pc .pc-review-note { margin: 16px 0; }
.pc .pc-review-note-body { margin: 8px 0 0; white-space: pre-wrap; overflow-wrap: anywhere; }
```

- [ ] Run the new tests and the affected existing families on the dedicated test DB:

```powershell
.venv/Scripts/python.exe docs/qa/place-qa01-fix-2026-10-10/run.py test catalog.testcases.test_place_rejection_feedback catalog.testcases.test_task33_place_continuous catalog.testcases.test_task33_publication catalog.testcases.test_task33_r1_owner_safety
.venv/Scripts/python.exe docs/qa/place-qa01-fix-2026-10-10/run.py check
git diff --check
```

Record counts, skipped tests and exit codes. Classify unrelated failures only after fresh baseline comparison; do not broaden the fix automatically.

## Task 3: Rendered acceptance and evidence

- [ ] In Chromium, repeat full owner creation/submission and moderator rejection through the real forms. Assert exact note visible → reload → logout/login → correct description → explicit save → reload → note still visible → resubmit → pending and obsolete note hidden. Read back DB reason/status/version at each transition.
- [ ] Reject a second time with different text and verify only the second reason. Cover ordinary rejection and final decline, standalone place and an organization-owned branch accessible under the existing ACL.
- [ ] Check RU/AZ/EN at 390/768/1024/1280/1440. Include a long multiline reason and long unbroken token; verify wrapping/overflow, contrast, content visibility, keyboard focus, form save and sticky navigation. Inspect DOM and screenshots, not source alone.
- [ ] Confirm escaped synthetic HTML has no active script/image/event-handler nodes. Check outsider/anonymous access and public-page non-disclosure in browser smoke checks. Do not change those screens.
- [ ] Capture console/network issues and blocked external traffic separately. Save screenshots for rejection, reload/new login, saved correction and resubmitted state; name each file with run/locale/width/state. Keep complete matrix results in JSON.
- [ ] Save `REPORT.md`, `command-ledger.jsonl`, `snapshot.json`, `isolation.json`, sanitized DB readback booleans, test summaries, browser matrix, screenshots and final preservation/diff verification in the new evidence directory. Preserve failed attempts and attribution.
- [ ] Report explicit NOT RUN: production, deployment, real external integrations and full unrelated application suite. Include any browser/locale/viewport gate that could not actually run.

Acceptance requires the new regression tests and the real browser roundtrip to pass on the recorded source snapshot, with existing data/stands and incoming worktree changes preserved. Do not mark PLACE-QA-01 fixed before those gates.
