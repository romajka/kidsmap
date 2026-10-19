import json
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=Path(__file__).resolve().parent;Q=R/'.tmp/site21-pc-fix-r1';P=R/'docs/qa/site-qa21-recheck-2026-10-18-pc-r1'
assert (O/'evidence/setup.json').exists()
runtime=(Q/'runtime.py').read_text();needle="elif command in ('serve','errors-serve','stage2-serve'):\n";assert runtime.count(needle)==1
runtime=runtime.replace(needle,needle+"    if command == 'serve': (QA/'server.pid').write_text(str(os.getpid()))\n")
runtime=runtime.replace("elif command == 'test':\n", "elif command == 'test':\n    assert str(settings.MEDIA_ROOT)=='/tmp/site21-pc-fix-r1-test-media' and str(settings.PRIVATE_MEDIA_ROOT)==str(QA/'test-private-media')\n    assert settings.CACHES['default']['LOCATION']=='m10s21-fix-r1-test'\n    (QA/'test-isolation.json').write_text(json.dumps({'testing':settings.TESTING,'test_DB':settings.DATABASES['default']['TEST']['NAME'],'test_media':str(settings.MEDIA_ROOT),'test_private_media':str(settings.PRIVATE_MEDIA_ROOT),'own_separate_test_cache':True,'normal_fixture_storage_not_used':True},indent=2))\n")
(Q/'runtime.py').write_text(runtime)
settings=(Q/'qa_settings.py').read_text()+"\n# Own test storage/cache are separate from the normal QA fixture.\nif len(__import__('sys').argv)>1 and __import__('sys').argv[1]=='test':\n    MEDIA_ROOT=__import__('pathlib').Path('/tmp/site21-pc-fix-r1-test-media')\n    PRIVATE_MEDIA_ROOT=QA_ROOT/'test-private-media'\n    CACHES['default']['LOCATION']='m10s21-fix-r1-test'\n"
(Q/'qa_settings.py').write_text(settings)
driver=(P/'browser_driver.py').read_text().replace('site21-pc-plan-r1','site21-pc-fix-r1');(O/'browser_driver.py').write_text(driver)
original=(P/'browser-acceptance.js').read_text();(O/'browser-acceptance.js').write_text(original)
observed=original.replace('local_errors=[],blocked=[];','local_errors=[],console_errors=[],blocked=[];').replace("p.on('pageerror',e=>pageerrors.push(String(e)));","p.on('pageerror',e=>pageerrors.push(String(e)));p.on('console',m=>{if(m.type()==='error')console_errors.push(m.text());});").replace('return{rows,pageerrors,local_errors,blocked,','return{rows,pageerrors,local_errors,console_errors,blocked,')
for phase in ['red','green']:(O/('browser-acceptance-'+phase+'.js')).write_text(observed.replace("'/png/acceptance-'","'/png/"+phase+"-acceptance-'"))
(O/'native-code-provenance.json').write_text(json.dumps({'prepared_PLAN_script_retained':True,'instrumentation_only':'console diagnostic collector added identically to RED/GREEN; check definitions unchanged','phase_difference':'PNG prefix only','no_class_style_template_transport_override':True},indent=2))
for name in ['qa_settings.py','runtime.py','qa_urls.py','seed.py','proxy.py']:(O/name).write_bytes((Q/name).read_bytes())
(O/'evidence/bootstrap-initial.json').write_bytes((Q/'bootstrap-initial.json').read_bytes())
(O/'prepare_bootstrap.py').write_bytes((Q/'prepare_bootstrap.py').read_bytes())
print('Own runtime prepared; normal/test storage separated; same RED/GREEN geometry checks, PNG prefixes only differ')
