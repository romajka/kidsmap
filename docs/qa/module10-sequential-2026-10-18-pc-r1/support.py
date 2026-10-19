import json,re,subprocess
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=R/'docs/qa/module10-sequential-2026-10-18-pc-r1';Q=R/'.tmp/m10-seq-r1';S=O/'stages/SITE02';S.mkdir()
(S/'evidence').mkdir();(S/'candidate').mkdir();(S/'entry-source').mkdir()
for path in ['src/catalog/templates/pages/about.html','src/catalog/templates/catalog/place_list.html']:
 p=S/'entry-source'/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((R/path).read_bytes())
(Q/'test_site02_candidate.py').write_bytes((R/'.tmp/site02-tests.py').read_bytes());(S/'test_site02_candidate.py').write_bytes((R/'.tmp/site02-tests.py').read_bytes())
(S/'IMPLEMENTATION_PLAN.md').write_text('''# SITE02 Implementation Plan — authorized sequential module10 work

**Goal:** Saved localized About/empty-result text must appear publicly for AZ/RU/EN.
**Architecture:** Existing SiteSettings i18n/context values remain the source of truth; remove template branches that take precedence over them. Blank values retain existing context defaults; retain automatic HTML escaping.
**Scope:** src/catalog/templates/pages/about.html, src/catalog/templates/catalog/place_list.html, new src/catalog/testcases/test_site_qa02_public_copy.py. No model/schema/permissions/CSS/JS/PO change. Concrete root and affected template blocks reviewed; narrow branch-priority change only.
**Authorization:** User explicitly requested analysis and immediate fixes for the listed15findings in order; no repeated approval required. No commit/push/deploy/production.

- [ ] Run complete4method regression in own scratch against unchanged source; confirm context values are saved but AZ public text fails.
- [ ] Change About to if site_about_text first, then existing localized literals; change empty heading to if site_empty_results_text first, then AZ/localized literals. Existing context fallback is authoritative for all3languages; no copied fallback rules in JS/model.
- [ ] Copy exact reviewed regression module (test_site02_candidate.py) into the stated new test file; record before/after hashes/diff.
- [ ] Fresh GREEN4methods plus relevant existing public wiring tests with same envclear/DJANGO_TESTING=1, disposable PG/cache/media/current3locales/integrationsdisabled.
- [ ] Actual-source native admin-save→publicreadback in3languages; configured/blank/default/escaped copy; affected pages at360/390/768/1024/1280/1440, layout/focus/console/network. No injected styles, rewritten responses or fake DB equality.
- [ ] Verify source/previous packages/refs/index/foreign runtimes, record exact executed and NOT RUN; preserve synthetic fixtures/logs, append progress, continue SITE03 under same user authorization.
''')
cmd=['docker','exec','m10seq-r1-app','python',str(Q/'runtime.py'),'test','test_site02_candidate'];r=subprocess.run(cmd,capture_output=True,text=True);raw=r.stdout+r.stderr;(Q/'site02-red.log').write_text(raw)
d={'command':cmd,'exit':r.returncode,'summary':[x for x in raw.splitlines() if x.startswith(('Found ','Ran ','FAILED','OK'))],'failures':re.findall(r'^FAIL: (.*)$',raw,re.M),'errors':re.findall(r'^ERROR: (.*)$',raw,re.M)}
(S/'evidence/red-backend.json').write_text(json.dumps(d,indent=2));print(json.dumps(d,indent=2));assert r.returncode==1 and d['failures'] and not d['errors'],raw[-2000:]
(O/'support.py').write_bytes(Path(__file__).read_bytes())
