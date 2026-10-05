import hashlib,json,shutil
from pathlib import Path
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[3]
old=Path('/root/km-completion-browser')
new=Path('/root/km-manual-mapfix')
assert new==Path('/root/km-manual-mapfix') and old!=new
if not new.exists():shutil.copytree(old,new,symlinks=True)
base=json.loads((HERE.parents[1]/'completion/final-verification.json').read_text())
files={item['path']:item['sha256'] for item in base['source_files']}
changed=['static/js/home_map.js','src/catalog/templates/pages/home.html','scripts/tests/home_map_tiles.test.cjs']
for name in changed:
    target=new/name;target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(REPO/name,target)
    files[name]=hashlib.sha256(target.read_bytes()).hexdigest()
for name,sha in files.items():
    for root in (REPO,new):assert hashlib.sha256((root/name).read_bytes()).hexdigest()==sha,name
result={'runtime_root':str(new),'baseline':'../completion/final-verification.json','change':'homepage OSM referrer and checked tile response handling',
    'changed_files':changed,'source_files':[{'path':name,'sha256':sha} for name,sha in sorted(files.items())]}
(HERE.parent/'source-manifest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'source_files':len(files),'changed_files':changed,'old_mirror_preserved':True}))
