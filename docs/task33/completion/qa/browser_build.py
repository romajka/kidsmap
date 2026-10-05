"""Copy retained verified browser harness without modifying previous evidence."""
from pathlib import Path
import shutil
ROOT=Path(__file__).resolve().parents[4]
OLD=ROOT/'docs/task33/qa28'
HERE=Path(__file__).resolve().parent
for p in OLD.glob('browser*'):
    if p.name in ('browser_build.py','browser_aggregate.py','browser_plan.md'):continue
    target=HERE/p.name
    if p.is_dir():shutil.copytree(p,target,ignore=shutil.ignore_patterns('__pycache__'),dirs_exist_ok=True)
    else:shutil.copyfile(p,target)
for p in HERE.glob('browser_*_bridge/commands.py'):
    text=p.read_text(encoding='utf-8').replace("parents[2]/'qa04/commands.py'","parents[3]/'qa04/commands.py'")
    p.write_text(text,encoding='utf-8')
p=HERE/'browser_launcher.py'
p.write_text(p.read_text(encoding='utf-8').replace("HERE.parent/'qa04/run.py'","HERE.parent.parent/'qa04/run.py'"),encoding='utf-8')
p=HERE/'browser_source.py'
text=p.read_text(encoding='utf-8').replace('parents[3]','parents[4]').replace("'docs/task33/qa28'","'docs/task33/completion/qa'").replace("domain.endswith('qa28')","domain.endswith('/qa')")
p.write_text(text,encoding='utf-8')
for name in ('browser_sync.sh','browser_run.sh'):
    p=HERE/name
    text=p.read_text(encoding='utf-8').replace('docs/task33/qa28','docs/task33/completion/qa')
    p.write_text(text,encoding='utf-8',newline='\n')
p=HERE/'browser_r1_matrix.js'
text=p.read_text(encoding='utf-8').replace("mode==='all'&&lang==='ru'&&width===390)await page.screenshot","mode==='all'&&lang==='ru'&&[390,1440].includes(width))await page.screenshot")
text=text.replace("role+'-ru-390.png'","role+'-ru-'+width+'.png'")
p.write_text(text,encoding='utf-8')
print('Copied retained harness into owned final-audit scope')
