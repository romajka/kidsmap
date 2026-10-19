import subprocess
from pathlib import Path
O=Path(__file__).resolve().parent;Q=O.parents[2]/'.tmp/site06-pc-fix-r1'
r=subprocess.run(['docker','exec','m10s06-fix-r1-app','python',str(O/'copy_owned_media_to_ram.py')],capture_output=True,text=True);assert r.returncode==0,r.stderr;print(r.stdout,flush=True)
(O/'evidence/media-storage-handoff.json').write_bytes((Q/'media-storage-handoff.json').read_bytes())
p=Q/'qa_settings.py';s=p.read_text();needle="MEDIA_ROOT = QA_ROOT / 'media'\n";assert s.count(needle)==1;s=s.replace(needle,"MEDIA_ROOT = __import__('pathlib').Path('/tmp/site06-pc-fix-r1-media')\n");p.write_text(s)
p=O/'check_final_static.py';s=p.read_text();needle="str(settings.MEDIA_ROOT)==str(QA/'media')";assert s.count(needle)==1;p.write_text(s.replace(needle,"str(settings.MEDIA_ROOT)==str(Path('/tmp/site06-pc-fix-r1-media'))"))
print('Only owned QA settings/static assertion now select the verified copy in the same app tmpfs; all source/DB/media URLs unchanged.')
