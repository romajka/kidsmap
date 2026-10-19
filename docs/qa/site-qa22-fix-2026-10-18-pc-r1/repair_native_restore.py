import json
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=R/'docs/qa/site-qa22-fix-2026-10-18-pc-r1'
for n in ['browser-save-engine.js','browser-saves-az.js','run_browser_acceptance.py','evidence/browser-saves-az-cli.txt','evidence/acceptance-commands.json']:
 p=O/n
 if p.exists():
  d=O/'initial-restore-failure'/n;d.parent.mkdir(parents=True,exist_ok=True);d.write_bytes(p.read_bytes())
files=list((O/'png').glob('save-*.png'))
for p in files:
 d=p.with_name('failed-v1-'+p.name);assert p.resolve().is_relative_to(O.resolve()) and d.resolve().is_relative_to(O.resolve()) and not d.exists();p.rename(d)
s=(O/'browser-save-engine.js').read_text();assert 'fill(String(initial.values[field]))' in s;s=s.replace('fill(String(initial.values[field]))',"fill(initial.values[field]===null?'':String(initial.values[field]))");(O/'browser-save-engine.js').write_text(s)
(O/'evidence/QA-null-restore-correction.json').write_text(json.dumps({'failure':'Nullable public_favorites_minimum initialNone restored with String(null); Playwright number input rejects null text','classification':'QA restore fixture representation; application source unchanged','fix':'Use empty input for None/null; keep exact database-restoration expectation, destination assertions and all save-case assertions unchanged','preserved_failed_PNG':len(files),'initial_script_CLI_commands_preserved':True,'failed_run_counts':'Not counted as PASS; interrupted function returned no structured matrix','original_null_value_evidence':'evidence/browser-focused-red.json initial.values.public_favorites_minimum'},indent=2))
