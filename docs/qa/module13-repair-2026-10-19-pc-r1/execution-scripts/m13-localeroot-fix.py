from pathlib import Path
import json,sys
R=Path('/mnt/c/kidsmap');Q=R/'.tmp/m13-full-r1';O=R/'docs/qa/module13-repair-2026-10-19-pc-r1';S=O/'stages/qualitylocales';S.mkdir();(S/'evidence').mkdir()
raw=(R/'.tmp/m13-qa04-r3/test.log').read_text();assert 'Output must be a new descendant of checkout .tmp' in raw
(S/'evidence/red-r1.json').write_text(json.dumps({'exit':1,'failures':['Current locale compiler correctly refuses QA04 /tmp root; native compiler output must be a fresh owned repository .tmp descendant.'],'errors':[],'no_test_body_executed':True},indent=2));(S/'IMPLEMENTATION_PLAN.md').write_text('CROSS04: preserve both existing safety contracts. QA04 profile stays /tmp; current isolated locale compiler output is a separate unique repository .tmp/quality-<profile.name>/locales. No compiler/path guard changes. Local read-only source container mounts only this new locale parent RW. CI host profile can create it directly.\n')
p='scripts/run_isolated_quality.py';b=(R/p).read_bytes();needle=b"        locale = build(ROOT/'locale', profile/'locales', ['az','ru','en'], 'native')";assert b.count(needle)==1;after=b"        locale_parent = ROOT/'.tmp'/('quality-' + profile.name)\n        locale_parent.mkdir(exist_ok=True)\n        locale = build(ROOT/'locale', locale_parent/'locales', ['az','ru','en'], 'native')"
sys.path.insert(0,str(Q));from stage_apply import apply
apply('qualitylocales',{p:b.replace(needle,after)},'stages/qualitylocales/evidence/red-r1.json')
t=(R/'.tmp/m13-qa04-run-v3.py').read_text();t=t.replace("cid=run(['docker','run'", "locale_parent=R/'.tmp'/('quality-'+Path(root).name);assert not locale_parent.exists();locale_parent.mkdir()\ncid=run(['docker','run'")
t=t.replace("'--entrypoint','python',image", "'--mount',f'type=bind,source={S},target={locale_parent}','--entrypoint','python',image")
(R/'.tmp/m13-qa04-run-v4.py').write_text(t)
