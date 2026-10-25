# Admin editor parity repair

User authorization: fix the broken admin editor and make photo handling match the website. Preserve current data and unrelated changes. Baseline main: 79a9b7992e8357fb0c4daa369c1d5e8e6bc2cc96; production application: 1505964b0ffa0fac18d603d0479c36a575b18529.

- Reproduce actual admin add/edit layouts and compare the owner photo workflow. Codebase Memory index is dated 2026-10-16 and does not cover current changed files reliably; graph hints are checked against source.
- Add failing rendered-browser checks for usable full-width verification content and a single photo entry point; add a DOM regression for admin make-main swapping photos, matching the owner editor.
- Repair verification markup/grid; preserve real preview and language selection. Hide redundant legacy upload entry points only when the shared picker mounts. Keep native formset validation and private-draft transport.
- Implement cover/gallery swapping and keyboard-accessible gallery order/replace actions; preserve saved and unsaved photos, private drafts, caption fields and native save.
- Verify new/edit, photos add/replace/remove/order/main, private save/reopen, native save/reopen and real preview on isolated local fixtures. Check AZ/RU/EN desktop/mobile, overlaps, focus and errors.
- Run targeted Django/JS regressions with DJANGO_TESTING=1 and isolated DB/cache/media/email; save source snapshots/results in docs/qa. Apply the verified correction to the previously authorized deployment after local acceptance, using backup and exact revision checks.
