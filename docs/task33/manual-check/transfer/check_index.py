"""Read only the staged changes; report paths/counts, never matched values."""
import json,re,subprocess,zipfile,io
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
def git(*args):return subprocess.check_output(['git','-C',str(ROOT),*args])
names=git('diff','--cached','--name-only','--diff-filter=ACMR','-z').decode().split('\0')
patterns={
 'private-key':re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
 'github-token':re.compile(r'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{60,})\b'),
 'aws-access-key':re.compile(r'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b'),
 'google-api-key':re.compile(r'\bAIza[0-9A-Za-z_-]{35}\b'),
 'stripe-live-key':re.compile(r'\bsk_live_[0-9A-Za-z]{20,}\b'),
 'slack-token':re.compile(r'\bxox[baprs]-[0-9A-Za-z-]{25,}\b'),
}
issues=[]; archives=[];sizes=[]
batch=subprocess.Popen(['git','-C',str(ROOT),'cat-file','--batch'],stdin=subprocess.PIPE,stdout=subprocess.PIPE)
for name in filter(None,names):
 batch.stdin.write((':'+name+'\n').encode());batch.stdin.flush()
 header=batch.stdout.readline().split();size=int(header[-1]);data=batch.stdout.read(size)
 assert len(data)==size and batch.stdout.read(1)==b'\n'
 sizes.append((name,len(data)))
 if len(data)>100*1024**2:issues.append({'path':name,'kind':'GitHub-size-limit'})
 if re.search(r'(^|/)(\.env(?!\.example$)|id_rsa|id_ed25519)|\.(dump|sqlite3|pem|p12|key)$',name):issues.append({'path':name,'kind':'sensitive-filename'})
 def scan(path,body):
  if b'\0' in body:return
  text=body.decode('utf-8',errors='replace')
  for kind,p in patterns.items():
   for m in p.finditer(text):issues.append({'path':path,'line':text.count('\n',0,m.start())+1,'kind':kind})
 scan(name,data)
 if name.endswith('.zip'):
  with zipfile.ZipFile(io.BytesIO(data)) as z:
   files=[i for i in z.infolist() if not i.is_dir()]
   archives.append({'path':name,'entries':len(files)})
   for item in files:
    if re.search(r'(^|/)\.env(?!\.example$)|\.(dump|sqlite3|pem|p12|key)$',item.filename):issues.append({'path':name+'/'+item.filename,'kind':'archive-sensitive-file'})
    if item.file_size<8*1024**2:scan(name+'/'+item.filename,z.read(item))
batch.stdin.close()
assert batch.wait()==0
report={'status':'PASS' if not issues else 'REVIEW','staged_added_modified':len(sizes),'largest':sorted(sizes,key=lambda x:x[1],reverse=True)[:5],
 'pattern_check':'Private-key/GitHub/AWS/Google/Stripe/Slack formats and sensitive filenames; not a proof of absence of every possible secret',
 'archives':archives,'findings':issues,'removed_from_tip_local_files_preserved':['.env#','backups/db.sqlite3.before-migrate-20260831-151210']}
(Path(__file__).parent/'index-review.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
if issues:raise SystemExit(1)
