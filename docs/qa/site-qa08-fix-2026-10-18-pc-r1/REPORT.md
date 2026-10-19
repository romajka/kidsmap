# SITE-QA-08 — применённый patch и незавершённая приёмка, 2026-10-18

**Exact approved2file patch APPLIED; SITE08 остаётся OPEN.** Основные формы исправлены, но after-save notification на RU360 расширяет документ до366px. Подготовлен [отдельный one-CSS followup](followup/IMPLEMENTATION_PLAN.md) /[точный diff](followup/proposed.diff); он **НЕ ПРИМЕНЁН**. Новая отдельная [SITE22/P3](findings/SITE-QA-22.md): «Сохранить и выйти» возвращается в subsection editor. Module10 теперь **15OPEN (10P2/5P3)**, full acceptance pending. Ложного CLOSED/полного GREEN нет.

Execution /root inline в canonical frontend-admin/orchestrator scope; independent specialist review NOT RUN. User «дальше» непосредственно после вопроса о применении конкретного SITE08 плана — authorization.json. LOCAL HEAD852938d96764ae315b92859e3651e5ea62054a36, branch codex/module09-transfer-2026-10-16-r1; dirty WORKTREE сохранён. Production UNKNOWN/не контактировали.

## Применено

Точно approved implemented.diff (SHA b19111c30e283d2514c81b649e73fd1de8409556de73dc4e132a0bb9f7234c0a): shared_settings_change_form.html root col-12/marker/editable flag +link, новый scoped kidsmap_settings_forms.css. Template e3791aa31eba0d31ecd14ce559cfca8745185b9ba3950dcc4aa92d224e5cbe29; CSS baf70032e5b918a783c136b4fa9449855c6eafb18df13f015a7ff144c7367f83. Source1033:1existing changed/1new/1031others unchanged, application refinements0. Global shell CSS/JS/backend/model/schema/PO/permissions/revision semantics не менялись. Full Git diff с HEAD также содержит прежние dirty edits; наш exact patch считается от fresh entry.

## Проверки и пределы

| Набор | Факт |
| --- | --- |
| Actual-source RED9forms×3langs×6widths | 820PASS314expectedFAIL /1134checks |
| Тот же actual-source GREEN | 1134/1134PASS,162cases |
| Readonly catalogue18cases | 126/126PASS до/после |
| Place/Event12native neighbor cases | 48baselinePASS →60PASS включая exactgeometry parity/no scoped CSS/marker |
| Native mobile JSON /both buttons /all3malformed fields/retries | 354/354PASS,48rows |
| Long1024char/nestedUnicode JSON/editor+readonly/native restore | 186/186PASS,20rows |
| Native mobile JSON errors/focus/bounds unique screenshots | 126/126PASS,18cases |
| Native field-linked central file errors/anchor focus | 72/72PASS,12cases |
| Viewer negativePOST403/deniedGET403/no writes | 7/7PASS |
| Existing backend regression suite | 105tests/33.566s/OK/exit0 |
| Actual source compile/current locale/CSS | 18permission-model roots,9active consumers,1033source hashes, current3root locales, CSSHTTP200/exactSHA |

Native media/footer62rows дали355PASS25FAIL; original assertions/results сохранены. Native image/email/gallery valid save/reload/public SSR values, invalid no-write/retry и actual Select2 longest existing option/open/Escape работают. Из25FAIL:12wrong hidden duplicate `.errorlist` targets,12real Save-exit mismatches SITE22,1real saved-message overflow remainingSITE08. Дополнительная ошибочная inline-error assumption дала12FAIL: actual error text существует в видимом central field-linked summary, inline container содержит только hidden duplicate list. Correct field-linked visibility/native focus затем подтвердились72checks. Эти failed datasets не переписывались/не удалялись.

Public JSON suite15PASS3FAIL: native mobile POST/reload/LogEntry/publicGET200 прошли, uppercase raw district expectation не совпала с lowercase public label. Source public_filter_options.py85–213 строит districts по published Place counts; presence `site08 qa district` не доказывает consumption districts_json. **Controlled native JSON→public dependency UNVERIFIED/manual_review**; ложный новый finding не создан и assertion не заменён ради green. Одна own synthetic published Place создана existing factory только как fixture foundation, не как native publication transition.

Raw actual-source aggregate2535checks: **2495PASS/40FAIL**. Классификация40:13real (remainingSITE08one +SITE22twelve),27incorrect/unsupported QA observations retained. Поэтому aggregate GREEN не заявляется. Details failure-classification.json /verification.json /matrix.csv. Все datasets без pageerrors/неожиданных localHTTPerrors; negative403 ожидаемые; external fonts blocked/ERR_FAILED диагностированы, console-clean не заявляется.

## Остаточный дефект и следующий scope

Native RU360 `_continue`, brand qa_ru_360, footer qa_ru_360_continue@example.invalid: стандартный Jazzmin message состоит из anonymous flex text/link. Baseline document366, временный scoped normal-flow CSS360, rollback366;14controlsPASS и unchanged fixture во время style probe. [PNG до](png/followup-alert-baseline-ru-360.png) /[прототип](png/followup-alert-prototype-ru-360.png). Followup меняет только existing CSS, не template/backend/navigation; candidate074e3405a541bc9c0ce6eaefea013388d48e810d2d9a48eb3a4bb7c940d7474c, diff da5563bc9a2e2d75f6cdf8ffa2b7c1992c440ff2ccbc0d5a2eb8678cd77dde99. DOM prototype не applied-source GREEN. До решения пользователя этот CSS не записан в приложение.

SITE22 native chain302POST→302GET changelist→200GET same editor, data/LogEntry correct; site.py untouched versus entry. Это отдельный pre-existing navigation issue/P3, не CSS regression. Нужен отдельный Django plan, не расширение текущего diff.

## Изоляция и сохранность

Own33580, normal/test separate DB/cache/media/private-media, locmem email; env clear/current source+locale guard до setup, integrations disabled. Test isolation proof/test IDs сохранены. Исходные JSON/scalar fields/image dimensions и прежние own gallery rows восстановлены native saves;84expected synthetic LogEntries, normalized uploaded file paths/bytes и owned media/public Place fixture оставлены на своём стенде. Не утверждается byte-identical restoration image under existing normalization. Ни одного foreign fixture cleanup/restart.

Сохранены34prior sealed packages/6763files, sharedMO/.cbmignore/refs/index/empty staging/activeNONE/foreign container IDs-state. Guide/MASTER append-only. SITE01/15/06/19/21 и module09 composite LOCAL closures retained; SITE20/SITE11 остаются отдельными OPEN.239PNG, named visual-review, commands/exits/manifests сохранены. Первый sentinel-route failure, screenshot9within-run overwrite и оба ошибочных error observers сохранены/объяснены; supplemental18unique JSON states доступны. WSL Git отметил74CRLF lines как trailing whitespace; exact approved bytes preserved/no whitespace bypass, Windows diffcheck0 и отдельный no-spaces-before-CRLF auditPASS. No commit/push/deploy/production/global/module11.

Следующий шаг — одобрить только конкретный one-file followup, затем fresh own native sourceRED→apply→GREEN по его плану. AGENTS.md требует «Future implementation requires a concrete plan and user approval for its scope»; дополнительного alert rule в первоначальном согласованном diff нет.
