"""Documentation-only closure; never run application or modify inherited evidence."""
import collections
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[4]
OUT=ROOT/'docs/task33/final-audit'
def read(name): return json.loads((OUT/name).read_text(encoding='utf-8'))
def write(name,value): (OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

image=read('image-full-r2-results.json')
suite=image['suite-results.json']
assert (suite['tests_run'],suite['failures'],suite['errors'],suite['skipped'])==(1817,108,12,0)
assert image['run.json']['cleanup']=='PASS'
image_scope='Exact V3 image: 1817 tests, 108 failures, 12 errors, 0 skip; Task33 580/580 PASS. Host Task33 579/580 remains: ownership race differs without source changes. Common 108 failing IDs; image-only taxonomy fixture reads docs/product omitted from frozen artifact. Full suite is not green. Image guards and cleanup PASS.'
stages=read('stage-map.json')
stage28=stages['stages'][-1]
stage28['current_runtime_gates']['image_full']=image_scope
stage28['source_refs'].append('docs/task33/final-audit/image-full-r2-results.json')
write('stage-map.json',stages)
requirements=read('requirements-review.json')
for record in requirements['requirements']:
    if record['id'] in ('R28-01','R28-02','R28-03','R28-05','R28-07','R28-10'):
        record['evidence'].append({'kind':'FRESH_EXACT_IMAGE_FULL_ATTRIBUTED','ref':'image-full-r2-results.json','executor':'/root/stage28_release','observed_scope':image_scope})
    if record['id']=='R28-05':
        record['covered_subclauses'].append({'scope':image_scope,'status':'VERIFIED_CURRENT_LOCAL_IMAGE_RUNTIME_PARTIAL_FULL_SUITE'})
        record['limitations']=['Full suite remains 108F12E; Task33 image PASS does not erase host ownership-race failure. Production private volume transition, pilot and real providers NOT_RUN.']
        record['uncovered_subclauses']=record['limitations'][:]
requirements['metadata']['fresh_image_attributed']='image-full-r2-results.json:1817/108F12E/Task33580; host579 retained'
write('requirements-review.json',requirements)

helper=OUT/'qa/domain_review_write.py'
text=helper.read_text(encoding='utf-8')
start=text.index('[stage-map.json]')
end=text.index('\n\n## 2.',start)
text=text[:start]+'''[stage-map.json](stage-map.json) содержит 28 строк с обещанием, реализацией, связями, source и точными test IDs. [requirements-review.json](requirements-review.json) содержит 306 индивидуальных записей: 220 имеют текущие узкие assertion scopes; ещё один содержит failed subclause ownership race; 52 относятся к историческому scope. Один пункт фиксирует product gap, один — mail crash window, один — незакрытую общую приёмку. Для 11 браузерных пунктов сопоставлены реальные действия и размеры экранов, но строгая браузерная проверка FAIL. Остальные 19 имеют конкретные role/source/workflow/external boundaries. Все прежние generic unverified записи заменены точными рассмотренными scopes. Настоящие assertions и результат их выполнения связаны с каждым выбранным тестом. Это **не 306 PASS**.

Свежий exact image: **1817 тестов, 108 failures, 12 errors, 0 skip; Task33 580/580 PASS**, guards и cleanup PASS. Исполнитель `/root/stage28_release`, [image-full-r2-results.json](image-full-r2-results.json). Первоначальные 125F/28E сохранены как история диагностированного QA harness. Host 579/580 остаётся действующим результатом: тот же ownership race проходит в образе без изменения source. Совпадают 108 failing IDs; дополнительная ошибка образа — тест taxonomy читает `docs/product`, намеренно отсутствующий в application artifact. Полный suite остаётся красным.

Свежий браузер: **816 contexts, 1724/1724 business/DOM checks PASS; strict FAIL** из-за одного `InvalidStateError` ViewTransition. Проверки R1/Specialist/Event охватывают AZ/RU/EN и семь ширин; Program/public Activity/public Organization — только 390/1280. Нативные POST проверки Program impact confirmation, candidate-only edit, stale 409, scope 404 и закрытые pending/private страницы прошли. Начальные approved display fixtures созданы ORM: полного публикационного UI-пути это не доказывает. [domain-browser-evidence.json](domain-browser-evidence.json) и [browser-results.json](browser-results.json). Из 1724 итоговых проверок 1721 представлены raw named UI checks; ещё три — collector checks Event. Их нельзя выдавать за дополнительные самостоятельно рассмотренные UI assertions.''' +text[end:]
text=text.replace('4. Для11renderedclauses сопоставить завершённыеbrowsercontexts/actions; дляостальныхsource/externalgates сохранить конкретнуюграницу.', '4. Исправить и повторить строгую браузерную проверку ViewTransition; расширить Program/Activity/Organization с двух ширин до обещанного набора. Для остальных source/external gates сохранить конкретную границу.')
helper.write_text(text,encoding='utf-8')
exec(compile(text,str(helper),'exec'))

browser=read('domain-browser-evidence.json')
browser['named_raw_checks']=sum(len(f['checks']) for f in browser['families'])
browser['aggregate_collector_checks_not_named_ui']=browser['checks']-browser['named_raw_checks']
write('domain-browser-evidence.json',browser)
runtime=read('domain-results.json')
runtime['helper_sha256']={str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((OUT/'qa').rglob('domain*.py'))}
write('domain-results.json',runtime)
print('Documentation closure PASS; no APP/runtime mutation.')
