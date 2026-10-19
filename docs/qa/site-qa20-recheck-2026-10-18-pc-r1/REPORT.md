# SITE-QA-20 — следующий точный план, 2026-10-18

**SITE20/P3 CONFIRMED OPEN; exact2file PLAN READY / approval pending, NOT APPLIED.** [План](IMPLEMENTATION_PLAN.md), [точный diff](proposed.diff), [before/candidate hashes](candidate-manifest.json), [verification](verification.json).

LOCAL HEAD852938d96764ae315b92859e3651e5ea62054a36 / codex/module09-transfer-2026-10-16-r1; dirty1034sources unchanged. Режим bounded audit/plan; /root inline по canonical frontend-admin + Django permission verification, без independent-agent claim. User «дальше» продолжает module10; прошлое «применяем» относилось к SITE22, не к новому scope. Production UNKNOWN/не контактировали.

## Подтверждённая причина и влияние

`src/catalog/templates/admin/catalog/shared_settings_change_form.html:126` выводит обе Save buttons без проверки `has_change_permission`; строка15 добавляет mobile editable marker только при change permission. Backend уже передаёт нужные permission flags. Source assignment/inheritance и runtime registry подтвердили9потребителей:6section proxies, SiteAnalytics, CatalogContentSettings, SiteGalleryImage. Граф C-kidsmap ready, но generation2026-10-16T18:56:53Z и relevant coverage unavailable/metadata_changed; выводы проверены текущими исходниками/installed runtime, не графом.

Существующий view-only пользователь видит desktopSave, native click→403. У view+delete gallery лишнее Save; у add-only gallery настоящая форма добавления на mobile без Save из-за отсутствия editable marker. Это одна область представления разрешённых действий; server authorization bypass не обнаружен. Новых ACL/ролей/политик патч не вводит. P3: недоступные действия/непоследовательный UI, production impact UNKNOWN.

## Свежие проверки

- Новый стенд33620/m10s20-plan-r1-app, own normal/test DB, envclear/DJANGO_TESTING=1/current3locale before setup, RO source/ownRW scratch/separate test media-cache-email, integrations disabled. Existing QA PG/network identity/internal/no published PG verified; foreign app containers untouched.
- Backend8methods in2.582s/exit1:3failed methods/29failure observations,5passed,0errors. Readonly9consumers×3locales, delete-only and add-only marker fail as expected. Direct viewer/denied POST403, deniedGET, change-only actions, singleton forbiddenadd and gallery add-only denial of existing object PASS. Test bodies unchanged after observed RED.
- Actual-source75native rows/498checks:375controlPASS,123expectedRED. Failure breakdown:60permission_actions (54view-only+6delete/view),54empty-action-card,6missing add-only marker,3hidden mobile add-only Save. Roles/languages/currentGET200/no-overflow/deletion count controls preserved.3native catalog viewerPOST403/no row/log/media changes; baseline settings/gallery/media hashes/logcount identical after; adminLog0.27freshPNG,2visual samples reviewed.
- Pageerrors0; only3expected local403; expected blocked fonts.googleapis.com produces ERR_FAILED console diagnostics; no blanket console-clean claim.
- Candidate renderer uses actual20role/model contexts +16permission truth-table cases,180checksPASS; compiled only, no applied-source/native candidate GREEN. git apply --check and candidate testAST PASS. Initial static audit guessed +5CRLF insertion count and returned false; retained result, independent byte audit proves exactly4newCRLF lines/no loneLF. Candidate/test/native assertion bytes unchanged by audit correction.

## Предлагаемое изменение

Ровно2файла: existing shared template +new8method regression. Save groups/root marker follow change or add+add permission; omit empty action sidebar for pure view; preserve independent existing delete guard. Existing CSS handles mobile once correct marker supplied. No backend/ACL/model/schema/PO/CSS/JS/destination changes. Exact content in [diff](proposed.diff); candidate remains solely under QA package.

## Сохранность и границы

1034sources unchanged;39priorpackages/8134files/sharedMO/.cbmignore/HEAD/branch/task33/index bytes/empty staging/activeNONE/foreign container identities-state verified. Own settings/catalog/gallery/media state restored by being unchanged; only own login/language sessions and negative requests used, no successful native application writes. Synthetic migration/seed fixtures remain on own profile. Guide/MASTER append-only.

**Module10 remains13OPEN(9P2/4P3), full acceptance pending.** SITE01/15/06/19/21/08/22 and module09 LOCAL closures retained. SITE11/othercanonical findings remain OPEN. NOT RUN: implementation/GREEN/nativecandidate, fullmodule/global/release/production/module11/crossbrowser/WCAG/physicaldevices. No commit/push/deploy/production/cleanup. Next: user decision on exact2file plan, then fresh fix-profile RED→apply→122backend/native acceptance.
