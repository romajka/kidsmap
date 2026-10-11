from pathlib import Path
import subprocess
here=Path(__file__).resolve().parent
root=here.parents[2]
journal=here.parent/'module-acceptance-prompts.md'
data=journal.read_bytes()
assert data.count(b'owner coordinate positive not confirmed. ')==1
journal.write_bytes(data.replace(b'owner coordinate positive not confirmed. ',b''))
head=subprocess.check_output(['git','show','HEAD:docs/qa/module-acceptance-prompts.md'],cwd=root)
old=head.splitlines();new=journal.read_bytes().splitlines()
assert len(old)==len(new)
assert [i for i,(a,b) in enumerate(zip(old,new)) if a!=b]==[20]
cli=Path.home()/'AppData/Local/npm-cache/_npx/31e32ef8478fbf80/node_modules/@playwright/cli/playwright-cli.js'
p=subprocess.run(['node',str(cli),'-s=module01-r1','close'],capture_output=True,text=True,encoding='utf-8',errors='replace')
(here/'browser-close.txt').write_text(p.stdout+'\nNative exit: '+str(p.returncode),encoding='utf-8')
assert p.returncode==0
print('Only row01 changed; own browser session closed; QA server/container retained')
