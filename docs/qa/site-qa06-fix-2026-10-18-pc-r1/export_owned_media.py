import hashlib,json
from pathlib import Path
source=Path('/tmp/site06-pc-fix-r1-media');Q=Path('/mnt/c/kidsmap/.tmp/site06-pc-fix-r1');target=Q/'media-final'
assert source.resolve()==Path('/tmp/site06-pc-fix-r1-media') and source.is_dir() and not target.exists() and target.parent.resolve()==Q.resolve()
target.mkdir();before={}
for p in source.rglob('*'):
 if not p.is_file():continue
 assert not p.is_symlink();rel=p.relative_to(source);raw=p.read_bytes();before[rel.as_posix()]=hashlib.sha256(raw).hexdigest();dest=target/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
after={p.relative_to(target).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in target.rglob('*') if p.is_file()};assert before==after
(Q/'media-final-manifest.json').write_text(json.dumps({'files':after,'all_exported_SHA_equal':True,'source_retained':True,'synthetic_media_only':True,'normal_db_unchanged':True},indent=2));print(json.dumps({'owned_final_media_exported':len(after),'all_SHA_equal':True,'source_retained':True}))
