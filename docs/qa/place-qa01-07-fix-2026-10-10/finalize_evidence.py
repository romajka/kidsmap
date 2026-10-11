"""Freeze final evidence, preserve original sources and record every native exit."""
import hashlib
import json
import subprocess
from datetime import datetime,timezone
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def run(*args):
    result=subprocess.run(args,cwd=ROOT,capture_output=True,encoding='utf-8')
    assert result.returncode==0,(args,result.returncode)
    return result.stdout.strip()
snapshot=json.loads((HERE/'snapshot.json').read_text(encoding='utf-8'))
preserve={path:sha(ROOT/path)==digest for path,digest in snapshot['source_before_sha256'].items()
          if path.startswith('docs/') or path.endswith('.mo')}
assert all(preserve.values()),preserve
head=run('git','rev-parse','HEAD');assert head==snapshot['head']
active=next(line for line in (ROOT/'docs/task33/implementation-status.md').read_text(encoding='utf-8').splitlines() if line.startswith('active_run:'))
assert active=='active_run: NONE'
foreign_now=run('wsl.exe','--exec','docker','ps','--format','{{.Names}} {{.Ports}}').splitlines()
foreign_preserved={row:row in foreign_now for row in snapshot['foreign_stands']}
assert all(foreign_preserved.values()),foreign_preserved
commands=[json.loads(line) for line in (HERE/'command-ledger.jsonl').read_text(encoding='utf-8').splitlines()]
browser=[json.loads(line) for line in (HERE/'browser-command-ledger.jsonl').read_text(encoding='utf-8').splitlines()]
secret=json.loads((ROOT/'.tmp/place-qa01-07-fix-20261010/credentials.json').read_text(encoding='utf-8'))
for file in HERE.rglob('*'):
    if file.is_file() and file.suffix in {'.json','.jsonl','.txt','.md','.py','.js'}:
        text=file.read_text(encoding='utf-8')
        assert not any(value['password'] in text for value in secret.values() if isinstance(value,dict)),file
screens=[{'file':file.name,'sha256':sha(file)} for file in sorted(HERE.glob('*.png'))]
(HERE/'screenshots-manifest.json').write_text(json.dumps(screens,indent=2)+'\n',encoding='utf-8')
final={'recorded_at_utc':datetime.now(timezone.utc).isoformat(),'head':head,'branch':run('git','branch','--show-current'),
       'active_run':active,'worktree':run('git','status','--short').splitlines(),
       'preserved_source_hashes':preserve,'foreign_stands_preserved':foreign_preserved,
       'final_source_sha256':{path:sha(ROOT/path) for path in snapshot['source_before_sha256']},
       'screenshots':len(screens),'production_accessed':False,'commit_push_deploy':False,'independent_agents_used':False,
       'runtime':{'postgres_port':55445,'http_port':8840,'DJANGO_TESTING':True,'compiler':'WSL GNU msgfmt 0.21','browser':'Chromium headless shell 153.0.8010.12'}}
(HERE/'final-snapshot.json').write_text(json.dumps(final,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
isolation=json.loads((HERE/'isolation.json').read_text(encoding='utf-8'))
isolation.setdefault('baseline_locale_paths',isolation['locale_paths']);isolation['locale_paths']=[str(ROOT/'.tmp/place-qa01-07-fix-20261010/locale-build-02/locale')]
isolation['compiled_assets']='Fresh GNU msgfmt assets; full content-hash manifest verified before Django.setup'
isolation['locale_manifest_sha256']=sha(ROOT/'.tmp/place-qa01-07-fix-20261010/locale-build-02/manifest.json')
(HERE/'isolation.json').write_text(json.dumps(isolation,indent=2)+'\n',encoding='utf-8')
lines=['# Exact native command ledger','', 'Commands were run from `C:/kidsmap`; browser cwd is the dedicated ignored scratch directory. Synthetic password arguments are redacted.','']
for title,rows in [('Native commands',commands),('Browser commands',browser)]:
    lines.extend(['## '+title,''])
    for index,row in enumerate(rows,1):
        args=row['argv']
        if 'run-code' in args:
            command=' '.join(args[:args.index('run-code')+1])+' <exact inline scenario retained in browser-command-ledger.jsonl>'
        else:command=' '.join(args)
        lines.append(f'{index}. Exit **{row["exit_code"]}** — `{command}`'+(f' → `{row["output_file"]}`' if row.get('output_file') else ''))
    lines.append('')
(HERE/'COMMANDS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps({'head_preserved':True,'shared_MO_and_plans_preserved':True,'foreign_stands_preserved':True,'secret_scan_passed':True,'screenshots':len(screens)}))
