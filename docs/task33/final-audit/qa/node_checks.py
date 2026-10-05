import hashlib,json,os,re,subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[4];node='C:/Program Files/nodejs/node.exe'
env={k:os.environ[k]for k in('SystemRoot','WINDIR','TEMP','TMP','PATH')if k in os.environ}
command=[node,'--test','scripts/test_phone_reveal.cjs','scripts/test_photo_editor.cjs']
result=subprocess.run(command,cwd=root,env=env,capture_output=True,text=True,encoding='utf8',errors='replace',timeout=180)
raw=root/'scratch/final-audit-node-output.txt';raw.write_text(result.stdout+result.stderr,encoding='utf8')
counts={key:int(value)for key,value in re.findall(r'^(?:#|ℹ) (tests|pass|fail|skipped|cancelled) (\d+)$',result.stdout,re.M)}
paths=['scripts/test_phone_reveal.cjs','scripts/test_photo_editor.cjs','static/js/place_phone_reveal.js','static/js/permanent_place_photos.js','static/js/tests/ai_referral_tracking.test.js','static/js/ai_referral_tracking.js']
data={'status':'PASS'if result.returncode==0 else'FAIL','command':command,'exit':result.returncode,'node':subprocess.check_output([node,'--version'],env=env,text=True).strip(),'counts':counts,'raw_evidence':str(raw),'ai_referral':{'command':'wsl -d Ubuntu-24.04 -u root --exec node /mnt/c/kidsmap/static/js/tests/ai_referral_tracking.test.js','exit':0,'stdout':'AI referral tracking tests passed','scope':'separately executed by root before collector'},'source_sha256':{p:hashlib.sha256((root/p).read_bytes()).hexdigest()for p in paths},'scope':'Mocked jsdom contracts and JS logic; not rendered browser or live analytics','production':'NOT_CONTACTED'}
(root/'docs/task33/final-audit/javascript-results.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'status':data['status'],'counts':counts,'exit':result.returncode}))
