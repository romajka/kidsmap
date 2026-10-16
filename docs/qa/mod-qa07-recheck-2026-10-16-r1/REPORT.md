# MOD-QA-07 — CONFIRMED OPEN / PLAN COMPLETE

**Баг воспроизведён. Приложение не изменено.** [План на3файла](IMPLEMENTATION_PLAN.md), [минимальный двухфайловый candidate diff](proposed.diff), [source/candidate hashes](proposal-manifest.json). Новый backend test — третий файл будущего approvedscope. Требуется отдельное одобрение пользователя.

## Snapshot и факт

Actual `/home/ramin/kidsmap`, HEAD `e4e05cc213b34e2d771ecb854901bfd016d1db51`, branch `task33-progress`, dirty WORKTREE, `active_run: NONE`. [Entry](entry.json). Historical module08 и прежняя module03LOCALприёмка не заменяют текущий recheck и не доказывают production.

**6nativecells RU/AZ/EN×390/1440,36observations:12sourceFAIL/24controlsPASS.** На каждойcell1inline required error становится84RU/83AZ/89ENsummarylinks с посимвольным HTML; href всехlinks `#`, Enter оставляетfocusнаA. Inline requiredvalidation, truthfulunsavedstatus, enteredrejected/longreason/emptycheckboxes и persistedunchanged — PASS. Все6Save фактически выполнены черезUI/nativeconfirmaccept→serverinvalid; status/requiredвалидация не обходились. [RU](native-ru.js.result.json), [AZ](native-az.js.result.json), [EN](native-en.js.result.json). Это sourcebaseline, не runtime/PO/harnessissue.

Причина: `change_form.html:13` итерирует AdminField.errors(), который возвращает renderedHTMLstring. Нужен field.field.errors underlyingBoundField. CheckboxSelectMultiple.id_for_label пуст, groupID задаёт auto_id; ссылка должна вести к группе, listener — focusпервый enabledvisiblecheckbox. Existinginline loop ужеBoundField, его не исправлять по старомуFAIL. Backend/model/AdminForm validation/privateACL/staleguard сохраняются. InstalledDjango6.0.2 helpers.py:199–200 и widgets checked; [BoundFielderrors](https://docs.djangoproject.com/en/6.0/ref/forms/api/#django.forms.BoundField.errors), [CheckboxSelectMultiple](https://docs.djangoproject.com/en/6.0/ref/forms/widgets/#checkboxselectmultiple) получены черезContext7. Runtimebrowser — основное evidence.

## Source/изоляция

Использован свой проверенный PostgreSQLserver ID из прежнегоownfixture; создана **новая собственная DB `mod07_plan_r1`**, собственныеcache/media/private-media/email/venv/locales/HTTP. НикакихPOST в старуюfixtureDB. Actualnative6invalidSave не изменили fullfieldSpecialist/M2Mspecializations/locations/documents; ownsession/lang менялись отдельно. OwnDB schema/migrate/seed — только подготовка нового syntheticstand; application source/schemafiles не изменены. [Profileownership](profile-reuse.json), [createDB](create-owned-db.txt), [prepare](prepare.txt), [runtimeinfo](runtime-info.json), [domainfinal](domain-final.json).

DJANGO_TESTING=1, envcleared доsetup, checkout.env/productioncredentials не загружались. BackendegressonlyownPG, browserownorigin; внешниеfontrequests явноblocked и отдельноdiagnosed. **0local console/page/network/HTTPerrors**. FreshRU/AZ/ENPO собраны ownisolatedhelper, manifestverified **доdjango.setup**, soleLOCALE_PATHS; actualopenedprojectMO и959currentappsourcefiles/templateorigins подтверждены [runtimefinal](runtime-source-final.json), [localemanifest](locale-manifest.json). SharedprojectMO unchanged.

Graph usedfirst: actualproject `home-ramin-kidsmap` rootverified, relevanttemplate/admin/actualJS/testmetadata_match/no_recorded_issue; hints notcompletenessproof. Не существующий inferredJSpath отброшен, фактическийscript найден изtemplate. Graphdata/cache не сохранялись вrepo. Lead выполняет ролиfrontend-admin/Django/browserпоследовательно, независимые агенты не заявляются.

## Команды, evidence, сохранность

[Commands/exits/durations](commands.jsonl): create_owned_db.py exit0; start.py build/verify/prepare/runtimeinfo exit0; browserdrive native-ru/az/en exit0, semanticFAIL отдельно; verify.py exit0=PLANgate, неFIXPASS. CandidateJS syntax и gitdiffcheck exit0. Первоначальная опечатка indentation вownQAhelper исправлена доruntimeevidence; [harnessnote](harness-note.json), к appfindings не относится. [Verification](verification.json), [PNG6manifest](png-manifest.json), RU390визуально просмотрен.

Послеentryполногоhashscan и финальной быстройidentityсверки **33310entryfiles unchanged**, missing0; единственное изменение внеownQAbundle — собственная insertedstatusnote вguide. Applicationchanges0, candidateappliedfalse. HEAD/branch/active_run unchanged. **1entryQAHTTP samepid/argv/cwd и74containers sameID/ports/state**. Старые3HTTP, исчезнувшие в предыдущемMOD06interruption, не перезапускались; их прежнееcontinuityNOTVERIFIED остаётсяисторией и текущим результатом не отменяется. [Preservation](preservation.json).

## Следующий шаг / NOT RUN

Approvedimplementation покаотсутствует. Доpatch — новыйцелевойbackendRED, затемexact3fileapprovedscope иtargetedGREEN. В будущем18singleerrorcellsallwidths плюсrepresentativemultiple/inline/focuscases иsharedstale/privateACLsubset; не полныйmodule03/08. Сейчас multiple/inline dynamiccases, candidatebrowserfeasibility, newbackendtests, patch/postpatchGREEN/full08/global/production NOT RUN. MOD08отдельныйPLAN; полный08одинразпослевсехзадач;module09/commit/push/deployзапрещены. ЗакрытыхIDэтимPLAN0.
