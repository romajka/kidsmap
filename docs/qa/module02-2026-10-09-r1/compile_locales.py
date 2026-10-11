from pathlib import Path
import subprocess,json,hashlib
here=Path(__file__).resolve().parent;root=here.parents[2]
dest=root/'.tmp/module02-20261009-r1/locale'
rows=[]
for language in ['az','en','ru']:
    source=root/f'locale/{language}/LC_MESSAGES/django.po'
    target=dest/f'{language}/LC_MESSAGES/django.mo';target.parent.mkdir(parents=True,exist_ok=True)
    args=['wsl','-d','Ubuntu-24.04','--','msgfmt',str(source).replace('C:\\','/mnt/c/').replace('\\','/'),'-o',str(target).replace('C:\\','/mnt/c/').replace('\\','/')]
    p=subprocess.run(args,capture_output=True,text=True)
    rows.append({'language':language,'argv':args,'exit_code':p.returncode,'po_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'mo_sha256':hashlib.sha256(target.read_bytes()).hexdigest() if target.exists() else None})
    assert p.returncode==0,p.stderr
(here/'locale-build.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
print('Compiled current PO into ignored own locale directory; repository MO unchanged')
