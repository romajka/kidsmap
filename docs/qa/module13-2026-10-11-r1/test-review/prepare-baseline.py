"""Read-only git archive into owned scratch; no checkout/worktree mutation."""
import hashlib,json,subprocess,tarfile
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[3]
S=ROOT/'.tmp/module13-20261011-r1/test-review';D=S/'head-donor';S.mkdir(parents=True,exist_ok=True)
archive=S/'head-source.tar'
command=['git','archive','--format=tar','-o',str(archive),'HEAD','src','static','locale','config','templates']
subprocess.run(command,cwd=ROOT,check=True)
D.mkdir(exist_ok=False)
with tarfile.open(archive) as handle:
    for member in handle.getmembers():
        target=(D/member.name).resolve()
        if not target.is_relative_to(D.resolve()) or member.issym() or member.islnk():
            raise RuntimeError('Escaping archive member')
    handle.extractall(D,filter='data')
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
tracked={f.relative_to(D).as_posix():hashlib.sha256(f.read_bytes()).hexdigest() for f in D.rglob('*') if f.is_file()}
same={rel:hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()==sha for rel,sha in tracked.items() if (ROOT/rel).is_file()}
mo=[]
# Frozen actual WORKTREE runtime .mo assets are untracked. Keep this baseline
# separate from a clean gettext build; report exactly this material limitation.
for original in (ROOT/'locale').rglob('*.mo'):
    target=D/original.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(original.read_bytes())
    mo.append({'path':original.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(original.read_bytes()).hexdigest(),'origin':'WORKTREE runtime binary, not tracked HEAD'})
(P/'baseline-source.json').write_text(json.dumps({'head':head,'donor':str(D),'git_archive_command':command,'tracked_count':len(tracked),'tracked_hashes':tracked,'same_as_worktree':same,'worktree_runtime_mo_copies':mo,'baseline_scope':'HEAD tracked application with frozen original WORKTREE runtime .mo assets; no claim of pristine gettext artifact baseline'},indent=2),encoding='utf-8')
print('HEAD donor tracked',len(tracked),'differs',sum(not x for x in same.values()),'frozen runtime MO',len(mo))
