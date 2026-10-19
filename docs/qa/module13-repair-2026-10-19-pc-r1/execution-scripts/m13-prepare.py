from pathlib import Path
R=Path('/mnt/c/kidsmap')
t=(R/'.tmp/m12-bootstrap.py').read_text()
t=t.replace("P=R/'docs/qa/module11-repair-2026-10-18-pc-r1'","P=R/'docs/qa/module12-repair-2026-10-18-pc-r1'")
t=t.replace("O=R/'docs/qa/module12-repair-2026-10-18-pc-r1'","O=R/'docs/qa/module13-repair-2026-10-19-pc-r1'")
t=t.replace("Q=R/'.tmp/m12-full-r1';old=R/'.tmp/m11-full-r1'","Q=R/'.tmp/m13-full-r1';old=R/'.tmp/m12-full-r1'")
start=t.index('def adapt(t):')
end=t.index('\nfor name in ',start)
t=t[:start]+'''def adapt(t):
 for a,b in [('m12-full-r1','m13-full-r1'),('m12full-r1','m13full-r1'),('m12full_r1','m13full_r1'),('m12_','m13_'),('M12','M13'),('module12','module13'),('33780','33810')]:t=t.replace(a,b)
 return t
'''+t[end:]
# Bootstrap infrastructure identifiers and assertions outside adapt's function.
head=t[:start];tail=t[start:]
for a,b in [('m12full-r1-app','m13full-r1-app'),('m12-full-r1-pg','m13-full-r1-pg'),('m12-full-r1-data','m13-full-r1-data'),('m12full_r1','m13full_r1'),('m12_guard','m13_guard'),('33780','33810'),('test_m12full_initial_r1','test_m13full_initial_r1')]:
 head=head.replace(a,b)
 # Do not replace adapt function's replacement source strings.
 end_adapt=tail.index('\nfor name in ')
 tail=tail[:end_adapt]+tail[end_adapt:].replace(a,b)
t=head+tail
t=t.replace("for name in ['proxy.py','playwright.json','seed.py','qa_urls.py']", "for name in ['proxy.py','playwright.json','seed.py','qa_urls.py','qa_simulation.py']")
t=t.replace("'HOST': 'm09full-r1-pg', 'PORT': '5432'", "'HOST': 'm09full-r1-pg', 'PORT': '5432'")
t=t.replace("wheel=old/'pypdf-6.20.1-py3-none-any.whl'", "wheel=R/'.tmp/m11-full-r1/pypdf-6.20.1-py3-none-any.whl'")
t=t.replace("(O/'authorization.json').write_text(json.dumps(","(O/'authorization.json').write_text(json.dumps(")
# No historical index-note assertions; current entry is the preservation baseline.
t=t.replace("'all1058_source_bytes_match_module11':True", "'all1066_source_bytes_match_module12':True")
t=t.replace("'Полностью проверить, проанализировать и исправить модуль12, включая новые связанные дефекты, завершить с приёмкой.'", "'Так же со следующим модулем: полностью проверить и исправить модуль13, включая подтверждённые связанные ошибки, завершить приёмку.'")
t=t.replace("'Analytics ingress/access/identity/privacy/storage resilience/periods/reporting/localization and affected public, owner, admin UI. Eight historical findings are checklist, not fresh failures. Concrete stages RED→fix→GREEN within existing authorization.'", "'Final cross-module reconciliation01–12, event lifecycle projections CROSS-QA-01, full discovery CROSS-QA-02, complete local regression and related confirmed failures; RED→minimal fix→GREEN. Current user request overrides historical plan-only prompts.'")
t=t.replace("(Q/'stage.json').write_text(json.dumps({'locales':'locales-current','test_db':'test_m13full_initial_r1'}))", "(Q/'stage.json').write_text(json.dumps({'locales':'locales-current','test_db':'test_m13full_initial_r1'}));(Q/'simulation.json').write_text(json.dumps({'report':'disabled','storage':'healthy'}))")
# Existing runtime's settings are already correct apart from own namespace/user.
t=t.replace(".replace(\"settings.DATABASES['default']['HOST'] == 'm09full-r1-pg'\",\"settings.DATABASES['default']['HOST'] == '127.0.0.1'\")", "")
t=t.replace("t=adapt((old/'runtime.py').read_text())", "t=adapt((old/'runtime.py').read_text())")
t=t.replace("t=adapt((old/'qa_settings.py').read_text())", "t=adapt((old/'qa_settings.py').read_text())")
t=t.replace("image=run(['docker','inspect','m11full-r1-app'", "image=run(['docker','inspect','m12full-r1-app'")
(R/'.tmp/m13-bootstrap.py').write_text(t)
print('Prepared own module13 bootstrap candidate; no source changes.')
