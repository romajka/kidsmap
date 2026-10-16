# SPEC-QA-01–03 repairs — LOCAL ACCEPTED

2026-10-13, approved plan docs/superpowers/plans/2026-10-13-module03-spec-qa01-03.md. Checkout /home/ramin/kidsmap, task33-progress, HEAD e4e05cc213b34e2d771ecb854901bfd016d1db51 +approved dirty WORKTREE; active_run NONE.

- SPEC-QA-01: before patch corrupt9-bytePNG saved/reloaded; validator now rejects corrupt/mismatched/truncated/encrypted/empty/oversized files before document writes; genuine PNG/JPEG/PDF original bytes preserved.
- SPEC-QA-02: saved photo normalized/copy-renamed during error clean; only new uploads normalized, persisted photo remains real canonical URL on409/400, newer data protected.
- SPEC-QA-03:8px styling restricted to progress track, header/nav readable at mobile widths.

RED18 methods/14 failure entries exit1, GREEN targeted91 PASS exit0 (runner21.029s), native scoped210PASS RU/AZ/EN×6widths, original assertions unchanged. Actual profiles/DB/cache/media/private-media/email/browser/locale root are own. Raw results, initial launcher/stale-locale errors and screenshots retained; no source patch for harness failures.

Full acceptance then exposed test portability and blank glyphs; both separately approved and verified. Authoritative final [module03 report](../module03-full-2026-10-13-r1/REPORT.md), [verification](../module03-full-2026-10-13-r1/verification.json), [reviewable diff](../module03-full-2026-10-13-r1/APPLICATION_DIFF.patch). No standalone repair result is a global/production PASS.
