# SITE-QA-22 — применено и проверено локально, 2026-10-18

**SITE22/P3 CLOSED LOCAL.** «Сохранить и выйти» из шести разделов ведёт прямо к существующим «Настройкам сайта» за один redirect; «Сохранить и продолжить» остаётся в редакторе. На hub длинное уведомление корректно переносится. Module10 теперь **13OPEN(9P2/4P3)**; полная приёмка модуля остаётся pending. Production UNKNOWN/не контактировали.

[Authorization](authorization.json): user «применяем» одобрил exactthree-file plan/diff. Execution /root inline, canonical Django/admin UI scope, no independent-agent claim. LOCAL HEAD852938d96764ae315b92859e3651e5ea62054a36, branch codex/module09-transfer-2026-10-16-r1, dirty WORKTREE сохранён. [План](IMPLEMENTATION_PLAN.md) и approved-candidate-manifest — исторические approved input с NOTAPPLIED; текущие [applied](applied.json), [diff](implemented.diff), [verification](verification.json) подтверждают применение.

## Применено

Ровно src/catalog/domain_admin/site.py: base.response_post_save_change→existing settings hub; static/admin/css/pages/kidsmap_site_settings.css: hub-only normal message flow/overflow-wrap:anywhere; новый src/catalog/testcases/test_site_qa22_save_exit.py с meaningful integration regressions. Exact diff SHAe60661fd4053bc76c501282f788a72351c8ea0d9f1f54ee7439343c260143e97. Application refinements0,1034sources:2existing changed/1new test/1031others unchanged. Model/schema/ACL/revisions/PO/global shell и SITE08 formCSS074e3405 не менялись. Analytics/catalogue/gallery остаются со своими destinations.

## Свежие результаты

| Проверка | Факт |
| --- | --- |
| Backend RED против исходного кода |9methods,3failed/6PASS,20expectedfailure observations/0errors,4.502s |
| Actual-source backend GREEN |114unique methods,33.601s,OK,exit0 |
| Same native focused RED→GREEN |78checks:72PASS/6expectedFAIL →78/78PASS |
| Sixsection native saves,3langs×6widths×both actions |216states +24long states,4086checks incl18native scalar restores,PASS |
| Readonly mobile/desktop baseline |126PASS,known desktopSITE20 retained |
| Place/Event marker/formCSS/hubCSS absence +exact geometry parity |72PASS |
| Invalid mobile JSON/draft/focus |126PASS |
| Invalid files/visible linked summary/native anchor focus/no-write |72PASS |
| Native invalid-email/stale valid-file409/oldtoken/draft/reselection |150PASS |
| Proxy-only editor/viewer/denied/missing-CSRF |129PASS; existing ACL retained |
| Native analytics/catalogue/gallery own destinations |225PASS |
| Console/bootstrap3langs×2widths×hub/footer/visibility |54PASS; externalfont errors explicitly classified |

**5118/5118actual-source native acceptance checks,435rows PASS.**240main save states: `_save`120times directPOST302→hubGET200, `_continue`120times directPOST302→same editorGET200. Exact persistence/1LogEntry, target marker/lang, reloaded field/fresh signed revision, no overflow, visible/wrapped message/link/close, keyboardTab/Enter close. Extra role/neighbour/stale writes recorded separately. Both CSSHTTP200/exactSHA;18permission/model template roots and hub compiled/current3root locales/source1034guard. No transport response rewrite, route.fetch or style injection in acceptance. Read-only console coverage is18cells, not every save; expected blocked externalfonts/ERR_FAILED retained, no console-clean claim. Expected403/409 are distinguished from unexpectedlocalHTTP; recorded pageerrors0.

## QA failure retained

Первый AZ80state run завершился только при восстановлении nullable minimum: test helper отправлял String(null) в number input. Structured matrix не вернулась, **PASS этого прерванного прогона не заявляется**. Original script/CLI/commands и80PNG сохранены (`initial-restore-failure`, failed-v1 PNG). Source допускаетnull/blank; исправлено только представление empty widget, destination/DB equality assertions не ослаблялись. Own nullable value восстановлен nativePOST302/1log,4controlsPASS; полныйAZ набор повторён и дал1362/1362PASS. RU/EN тоже1362/1362PASS. Ни одного дополнительного application diff.

## Изоляция и сохранность

Fresh own33610 /m10s22-fix-r1-app, normal m10s22_fix_r1, REDtest_m10s22_fix_r1 и отдельный freshGREENtest_m10s22_fix_green_r1. Envclear/DJANGO_TESTING=1/isolated normal-test cache/media/private-media/email/currentlocales/integrationsdisabled/ROrepo. Backend test data не используют normal fixture storage. Перезапущен только свой source-loaded server после проверки fullcontainerID/cmdline; все чужие стенды сохранены.

Изначальные6section scalar values,3JSON иgallery display values восстановлены native saves; logo/media filenames+bytes неизменны.419expected synthetic LogEntries:6REDfocused +85logdelta interruptedAZ +1nullable recovery +327successful acceptancePOST. Timestamps и журналы оставлены на own stand; byte-identical DB rollback не заявляется. Public SSR brand/footer exact readback прошёл; public JSON consumer dependency не предмет scope.

Уточнение восстановления: ORM seed содержал один конечный пробел в about_text_ru/az/en. Native About form использует существующий CharField(strip=True), поэтому эти3текста восстановлены к form-cleaned seed. [Read-only normalization proof](evidence/text-normalization.json) подтверждает актуальную форму/все3значения и byte-identical form code вне нового response hook. Это вывод о ранее существовавшей нормализации по неизменённому source, не наблюдение prepatch native About. Первоначальный final guard сравнивал с raw ORM seed; квалифицирован только этот доказанный trailing-blank случай, остальные values/media/route assertions сохранены. Raw trailing-whitespace restoration не заявляется.

Оригинальные10media files сохранили имена/байты. Native gallery caption save штатно вызвал существующий post_save prepare_responsive_photos→generate_variants и создал4WebP derivatives+manifest в собственном responsive-images cache. [Read-only cache audit](evidence/derivative-cache.json) сопоставил весь добавленный набор с source image, размерами и manifest. Эти5служебных файлов оставлены в own QA media; отсутствие новых cache files не заявляется. Исходники signals/responsive_images входят в1031unchanged; первоначальный inventory-equality guard ошибочно считал cache additions изменением оригиналов. Проверки исходных байтов, отсутствия удалений, gallery values и остальных полей сохранены.

38priorpackages/7576files/sharedMO/.cbmignore/refs/index bytes/empty staging/activeNONE/73foreigncontaineridentities-state проверены.442PNG incl80failed, [matrix](matrix.csv), [visual-review](visual-review.json), exact commands/exits/IDs/manifests сохранены. Guide/MASTER append-only. SITE01/15/06/19/21/08 иmodule09 LOCAL closures retained; SITE20/SITE11 иостальные canonical findings OPEN. Полный module10/global/production/cross-browser/a11y/physical device acceptance NOTRUN. Без commit/push/deploy/production/нового module11/чужого cleanup.
