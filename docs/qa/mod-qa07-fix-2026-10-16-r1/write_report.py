from pathlib import Path
import json,hashlib
h=Path(__file__).resolve().parent;r=h.parents[2];v=json.loads((h/'verification.json').read_text());pres=v['preservation'];e=json.loads((h/'entry.json').read_text());guide=r/'docs/qa/continuation-and-repair-prompts-2026-10-11.md';name=str(guide.relative_to(r));before=guide.read_bytes();assert hashlib.sha256(before).hexdigest()==e['files'][name]
note=f'- Module08 MOD-QA-07 **approved core LOCAL PASS / whole ID OPEN**, 2026-10-16: [REPORT]({h.name}/REPORT.md), [CSS supplement PLAN pending approval]({h.name}/CSS_SUPPLEMENT_PLAN.md). Approved2appfiles+NEWtest:2methods/6languageassertionFAIL RED→5target/sharedmethodsGREEN;126primarynativePASS/18cells+58edgesPASS(2explicitSIMULATED), persistedparent/M2M/locations/documentsunchanged. Newheadinglayout3mobileFAIL,6SIMULATEDCSSfeasibilityPASS; CSS unapplied.62PNG,current960source/ownfreshMO,2entryHTTP+74containers preserved;HEAD/branch/active_runNONE unchanged. No full08/global/09/production/commit/push/deploy.\n\n';marker='## Сколько задач осталось и как идти';assert marker in before.decode();guide.write_text(before.decode().replace(marker,note+marker,1));assert guide.read_text().replace(note,'',1).encode()==before;(h/'status-note.json').write_text(json.dumps({'path':name,'before':hashlib.sha256(before).hexdigest(),'after':hashlib.sha256(guide.read_bytes()).hexdigest(),'only_inserted_note':True},indent=2));pres['changed_entry_files'].append(name);pres['unchanged_files']-=1;(h/'preservation.json').write_text(json.dumps(pres,indent=2))
report=f'''# MOD-QA-07 — approved core LOCAL PASS / whole ID OPEN

**Посимвольные ошибки и переход к полю исправлены. CSS-проблема заголовка остаётся OPEN.** [Одобренный план](../mod-qa07-recheck-2026-10-16-r1/IMPLEMENTATION_PLAN.md), [approval](APPROVAL.md), [новое конкретное CSS-дополнение](CSS_SUPPLEMENT_PLAN.md) требует отдельного approval. Полный module08 NOT RUN; production не затрагивался.

## Snapshot и правка

`/home/ramin/kidsmap`, HEAD `{v['head']}`, branch `{v['branch']}`, dirty WORKTREE, `active_run: NONE`. [Entry fullstatus/hashes](entry.json). Исторические LOCAL/module03/production состояния не приравниваются к текущей проверке.

Два existingappfiles: specialist/change_form.html и specialist_admin.js, плюс NEWtest_mod07_specialist_error_summary.py. Template берёт ErrorList BoundField вместо renderedHTML AdminField и получает fallbackgroupauto_id; JS errorlinks выбирает enabledvisiblecontrol внутриgroup, либо focusablegroup сtabindex-1. Ordinaryinputs/sectionnavigation/inlineBoundFieldloop/validation/stale/privateACL сохранены. [Exact3filepatch](implementation.patch). ProductionCSS/PO/schema/adminforms/endpoints не менялись.

## Meaningful regression

Beforepatch новая группа3methods: **2failingmethods/6language assertionFAIL**,1inlinecontrolPASS. Ошибка required существует, но ожидаемые1/2links получались84/другойдлинныйcount. NativeRU390: **2sourceFAIL/4controlsPASS** (characterlinks + keyboardfocus), actualnativeSaveconfirm→serverinvalid. [BackendRED](tests-red.txt), [nativeRED](native-red.js.result.json).

Afterexactapprovedpatch **5methodsPASS**:3new(single/multiple/inline×RUAZEN) +2existingrepresentativeguards staleversion/privateinlinepermission. Existing/newassertions не менялись отRED. [BackendGREEN](tests-green.txt), [testhash](test-source-manifest.json). Никакие старые fullmodule03/08backendнаборы не повторялись.

**126actualprimaryPASS** RU/AZ/EN×360/390/768/1024/1280/1440:18cells actualSave/nativconfirm/serverinvalid; oneerror→onewholelink, inputstatus/reason/checkboxesretained, honestunsavedstatus, Enter→visiblecheckboxfocus+hit+focus-visible, nohorizontalclipping, persistedunchanged. [RU42](native-ru.js.result.json), [AZ42](native-az.js.result.json), [EN42](native-en.js.result.json).

[Edges58PASS](native-edges.js.result.json):actualmultiple/inline×390/1440all3langs; ordinarynameinput/inlinepricefocus, longescapedreason/noinjectedimg, nosideeffects. **2из58явноSIMULATED** disabled/hiddenfirstcheckbox→nextavailable иnocontrols→groupfallback, остальное56actualUI/controls. Reloadremovesclientsubstitutions, normalGETnoerror, sectionnavigationunchanged. Итогоapprovedbrowser **184PASS =182actual+2SIMULATED**, безповторастарогоfullcorpus. Allsubmittedformsinvalid: реальныеsuccessfulsave/delete/private-documentwritesNOTRUN.

## Новая причина / MOD07 не закрыт целиком

Визуальный просмотр actualRU390послеcorepatch выявилflexlayout: errorheading крупный, сжимается рядомсо спискомиразбиваетсянамногострок. CSS был прямоисключён изодобренногоплана. Неисправлялиегоавтоматически.

Fresh [layoutrecheck](native-layout-plan.js.result.json), RU/AZ/EN×390/1440: **3sourceFAILmobile +3desktopcontrolPASS**. Предлагаемые2scopedrules черезpage.addStyleTag дали **6explicitSIMULATEDfeasibilityPASS**, это НЕ sourceGREEN. SourceCSS hash осталсяentryhash; [candidate/diff](css-supplement.diff), [manifestappliedfalse](css-supplement-manifest.json). Supplementonlyonefile `static/admin/css/pages/specialist_form.css`:blocklayout иheading1rem. [ReviewablePLAN](CSS_SUPPLEMENT_PLAN.md). ПокаCSSapproval/patch/GREENиwholeMOD07closureNOTRUN.

## Evidence, runtime, сохранность

**62PNG** [hash/size/phase manifest](png-manifest.json), отдельноRED/coreGREEN/newactualCSSFAIL/SIMULATEDcandidate. Визуальнопросмотрены RU390error/focus иlayoutcandidate. **0localconsole/page/network/HTTPerrors**; externalfontsblockedявно, diagnosticsretained. [Commands/exits/durations](commands.jsonl): tests-redexit1(expected6FAIL), tests-greenexit0(5PASS), allnativeCLIexit0сотдельнымиsemanticcounts; layoutCLIexit0сампособенеPASS. Nodecheck/gitdiffcheck/finalgateexit0. [Semanticverification](verification.json).

ReuseтолькособственнойMOD07PLANfixtureDB послеownership/source/containerverification, безmigrate/reseed; отдельнаяtestDBtest_mod07_summary_fix_r1. НовыеownHTTP/cache/media/private-media/email/venv/locales. DJANGO_TESTING=1, envclearedbeforeSetup, checkout.envnotloaded, no productioncredentials; backendegressonlyownPG/browserownorigin. FreshownRUAZENPOcompiled/manifestverifiedbeforedjango.setup/soleLOCALE_PATHS/actualopenedMO; sharedprojectMOunchanged. Current960source files/templateorigins/liveprocessmatch. [Profile](profile-reuse.json), [runtimeinfo](runtime-info.json), [sourcefinal](runtime-source-final.json), [localemanifest](locale-manifest.json).

Specialistfullfield/M2Mspecializations/locations/documents/Place/Event fingerprint неизмененпосле18primary+12edge+6layoutinvalidPOST; authsessions/languageне входятвэтотdomainhash. [Before](domain-before.json), [after](domain-final.json).

**{pres['unchanged_files']}entryfilesunchanged**, missing0; измененытолько2approvedexistingappfiles+ownstatusnote; NEWtestотдельно.2entryQAHTTPsamePID/argv/cwd,74containerssameID/ports/state;HEAD/branch/active_rununchanged. [Preservation](preservation.json). Предыдущееисчезновение3HTTPвMOD06остаётсяисторическимcontinuityNOTVERIFIED, текущийsnapshotегонепереопределяет. Новыхпрерыванийнебыло.

## Далее

ОтдельноодобритьодинCSSfileпоsupplementPLAN; затемтолькоtargetedlayout/nativechecks иretainedsourceproofсуществующих5backend/184browserPASS, безповтораихполногокорпуса. MOD08отдельныйPLAN; fullmodule08одинразпослевсехзадач, globalотдельно. MOD09/production/commit/push/deploy/physicaldevices/nonChromiumNOTRUN. ЦеликомMOD07ещёOPEN, новыхзакрытыхисторическихIDэтототчётнеобъявляет.
''';(h/'REPORT.md').write_text(report);(h/'next-prompt.txt').write_text('Продолжить MOD-QA-07 после отдельногоapproval '+str(h/'CSS_SUPPLEMENT_PLAN.md')+'. Approvedcore3filesdone,5backend/184browserPASS retain byhash; wholeIDOPEN CSScause3mobileFAIL. CSSfileunapplied. CurrentHEAD e4e05cc213b34e2d771ecb854901bfd016d1db51 branchtask33-progress dirty active_runNONE verify. Source960/ownMOD07fixtureDB mod07_plan_r1/ownHTTPserver-current.json verify before reuse. NewCSSscopeonefile only, targetedchecks; full08onceaftertasks/globalseparate. Preserveallforeignfiles/processes/stands, no09/production/commit/push/deploy.\n');print('Core report and CSS-supplement scope saved; whole MOD07 remains OPEN')
