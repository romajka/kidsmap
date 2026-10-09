# Remaining organization QA fixes — approved local scope

User authorization: «делаем» after the four remaining findings. Local only; no commit/push/deploy. Preserve previous dirty work. Existing links, permissions and publication rules stay unchanged.

1. Branch pagination: preserve focused semantic control during replacement; disabled previous/next falls back to current page. Add aria-current. Search and initial render never steal focus. RED/GREEN DOM regression and native Enter/Space/Tab/Shift+Tab checks.
2. Owner places at768: constrain content width in existing one-column breakpoint. Diagnose with rendered geometry; test RU/AZ/EN×360/390/768/1440, scrollable navigation and actions.
3. ViewTransition aborted navigation: handle both fulfilled/rejected completion for cover cleanup. Register transition listeners in parser-blocking head; skip outgoing account destinations before their opt-out reveal. Keep public animation enhancement; no suppression of unrelated errors. RED/GREEN aborted/completed events plus native navigation/browser error capture.
4. Migration drift: inspect exact detector output without active translations. Only four AlterModelOptions for existing admin names; no SQL/data operations. Add explicit state-only migration, verify dry-run clean, forward/reverse SQL and isolated migration/test run. No production migration.

Acceptance/report: current HEAD/worktree/source manifest; exact fresh commands and failure boundaries; PC/mobile screenshots; preservation of existing domain fixture rows. Full-suite and real screen reader remain NOT RUN unless actually executed.

COMPLETE LOCAL:4 findings; server149+14 selected suites,JS38, browser336 focus/114 places/37 transitions/4 reduced/3 screenshots. Full suite and real screen reader NOT RUN. See docs/qa/org-followup-2026-10-09.md.
