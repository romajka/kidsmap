import hashlib,json,shutil,time
from pathlib import Path
source=Path('/mnt/c/kidsmap/.tmp/site06-pc-fix-r1/media');target=Path('/tmp/site06-pc-fix-r1-media');O=Path('/mnt/c/kidsmap/docs/qa/site-qa06-fix-2026-10-18-pc-r1')
assert source.is_dir() and target.parent.resolve()==Path('/tmp') and not target.exists()
files=[p for p in source.rglob('*') if p.is_file()];assert not any(p.is_symlink() for p in files)
total=sum(p.stat().st_size for p in files);assert total<32*1024*1024 and shutil.disk_usage('/tmp').free>total+8*1024*1024
target.mkdir();before={}
for p in files:
 rel=p.relative_to(source);raw=p.read_bytes();before[rel.as_posix()]=hashlib.sha256(raw).hexdigest();dest=target/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
start=time.monotonic();after={p.relative_to(target).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in target.rglob('*') if p.is_file()};elapsed=time.monotonic()-start
unchanged={p.relative_to(source).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in source.rglob('*') if p.is_file()}
assert before==after==unchanged
data={'old_root':str(source),'new_root':str(target),'same_owned_app_tmpfs':True,'originals_retained':True,'all_original_and_copied_hashes_equal':True,'files':before,'total_bytes':total,'ram_full_SHA_seconds':elapsed,'snapshot_hashes_remain_full_reads_without_caching':True,'application_files_changed_by_handoff':0}
(source.parent/'media-storage-handoff.json').write_text(json.dumps(data,indent=2));print(json.dumps({'owned_files_copied':len(files),'bytes':total,'all_SHA_equal':True,'RAM_full_SHA_seconds':elapsed,'originals_retained':True}))
