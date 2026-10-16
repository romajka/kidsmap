from pathlib import Path
import json,re
H=Path(__file__).resolve().parent;R=H.parents[2];OLD=R/'docs/qa/module07-2026-10-10-r1';port=json.loads((R/'.tmp'/H.name/'config.json').read_text())['http_port'];queue=[]
names=['matrix','modal-proof','auth-flow','auth-negative','acl','acl-boundaries','privacy-flow','team-flow','org-conflict-proof','api-contracts','access-transitions','deletion-relations','person-deletion','deletion-flow','cancel-recovery']
for name in names:
 s=(OLD/(name+'.js')).read_text().replace('http://localhost:8820',f'http://127.0.0.1:{port}').replace('C:/kidsmap/docs/qa/module07-2026-10-10-r1/screenshots/',str(H/'screenshots')+'/').replace('C:/kidsmap/.tmp/module07-20261010-r1/assets/',str(R/'.tmp'/H.name/'assets')+'/').replace('module07_r1_csrf','module07fullr1_csrf').replace('module07_r1_session','module07fullr1_session')
 s=s.replace('__FIXTURES_JSON__',"(await(await original.request.get(B+'/qa/fixtures/')).json())").replace("'__LOCAL_PASSWORD__'","PASSWORD")
 lines=s.splitlines();idx=next(i for i,l in enumerate(lines)if 'const B='in l);lines.insert(idx+1," const PASSWORD=(await(await original.request.get(B+'/qa/fixtures/')).json()).password;");s='\n'.join(lines)+'\n'
 if name=='acl':s=s.replace("'outsider','volunteer','moderator','reviewer','staff','admin'","'outsider','moderator','reviewer','staff'") # source-specific volunteer/admin expectations in boundaries
 if name=='person-deletion':s=s.replace("add('recipient-inbox-no-reject-control',false,","add('recipient-inbox-reject-controls-present',actions.filter(x=>x.action?.endsWith('/reject/')).length===2,").replace('ACTUAL missing UI controls, two synthetic invitations','ACTUAL current native reject controls, two synthetic invitations')
 if name=='matrix':
  s=s.replace("await p.waitForLoadState('domcontentloaded');add('login-error", "await p.waitForLoadState('networkidle');add('login-error")
  s=s.replace("await p.waitForLoadState('domcontentloaded');await capture('google-local-error')","await p.waitForLoadState('networkidle');await capture('google-local-error')")
 if name=='team-flow':
  a=s.index("const reject=await invite");b=s.index("  const cancel=await invite",a)
  s=s[:a]+'''const reject=await invite(F.actors.rejectee.email);await rejectee.goto(B+'/ru/account/notifications/');const rejectButton=rejectee.locator('form[action$="/reject/"] button');add('recipient-native-reject-offered',await rejectButton.count()===1,'rejectee',{screenshot:await shot(rejectee,'reject-inbox-native-ru-390')});await Promise.all([rejectee.waitForNavigation({waitUntil:'domcontentloaded'}),rejectButton.click()]);add('recipient-native-reject-status',(await state(owner)).invitations.find(x=>x.id===reject.id)?.status==='REJECTED','rejectee');
'''+s[b:]
  s=s.replace("await Promise.all([recipient.waitForNavigation({waitUntil:'domcontentloaded'}),save.click()]);", "const [staleSaveResponse]=await Promise.all([recipient.waitForResponse(r=>r.url().includes('/save-photos/')&&r.request().method()==='POST'),save.click()]);")
  s=s.replace("&&!recipient.url().endsWith('/edit/'),'invitee',{buttons", "&&staleSaveResponse.status()===403,'invitee',{http:staleSaveResponse.status(),buttons")
  s=s.replace("let response=await post(network,'/en/account/business/team/organization/'+F.organization+'/grant/',{grant_id:og.id,expected_version:og.version,role:'MODERATOR'});",'''await network.goto(B+'/en/account/organizations/'+F.organization+'/');const orgRole=network.locator('[data-team-operation="role"][data-grant-id="'+og.id+'"]');await orgRole.locator('[name=role]').selectOption('MODERATOR');const [responseRole]=await Promise.all([network.waitForResponse(r=>r.request().method()==='POST'&&r.url().includes('/grant/')),orgRole.locator('button[type=submit]').click()]);let response=responseRole;''')
  s=s.replace("add('organization-role-change-HTTP'","add('organization-role-change-native'")
  needle="response=await post(network,'/en/account/business/team/organization/'+F.organization+'/grant/',{grant_id:og.id,expected_version:og.version,active:false});"
  s=s.replace(needle,'''await network.reload();await network.locator('[data-team-confirm-open="org-grant-revoke-'+og.id+'"]').click();const orgRevoke=network.locator('[data-team-operation="revoke"][data-grant-id="'+og.id+'"]');[response]=await Promise.all([network.waitForResponse(r=>r.request().method()==='POST'&&r.url().includes('/grant/')),orgRevoke.locator('button[type=submit]').click()]);''')
  s=s.replace("add('organization-remove-HTTP'","add('organization-remove-native'")
  s=s.replace("await Promise.all([recipient.waitForNavigation({waitUntil:'domcontentloaded'}),recipient.locator('form:has([name=name_az]) button[type=submit]').first().click()]);", "const [orgStaleResponse]=await Promise.all([recipient.waitForResponse(r=>r.request().method()==='POST'&&r.url().includes('/save-photos/')),recipient.locator('form:has([name=name_az]) button[type=submit][value=save_draft]').first().click()]);")
  s=s.replace("&&!recipient.url().endsWith('/edit/'),'invitee',{screenshot:await shot(recipient,'org-employee-stale", "&&orgStaleResponse.status()===403,'invitee',{http:orgStaleResponse.status(),screenshot:await shot(recipient,'org-employee-stale")
  start=s.index("  add('organization-role-remove-native-UI'");end=s.index('\n',start);s=s[:start]+"  add('organization-role-remove-native-UI',response.status()===200,'network',{lang:'en',width:1440,screenshot:await shot(network,'organization-native-role-remove-en-1440')});"+s[end:]
 if name in ('matrix','modal-proof','auth-flow','acl','acl-boundaries','org-conflict-proof'):
  for lang in ('ru','az','en'):
   fname=name+'-'+lang+'.js';(H/fname).write_text(s.replace("['ru','az','en']","['"+lang+"']",1));queue.append(fname)
 else:(H/(name+'.js')).write_text(s);queue.append(name+'.js')
(H/'browser-queue.json').write_text(json.dumps(queue,indent=2))
p=H/'drive.py';s=p.read_text().replace("code=(HERE/sys.argv[1]).read_text()","code=(HERE/sys.argv[1]).read_text().replace('__EXPIRED_CODE__',(ROOT/'.tmp'/HERE.name/'expired-code').read_text())")
s=s.replace("raw=p.stdout+p.stderr","raw=(p.stdout+p.stderr).replace((ROOT/'.tmp'/HERE.name/'expired-code').read_text(),'[EXPIRED-OWN-CODE]')")
s=s.replace("raw=re.sub(r'(https?", "raw=re.sub(r'[0-9a-f]{8}-[0-9a-f-]{27,}','[OWN-ID]',raw,flags=re.I)\nraw=re.sub(r'([?&]token=)[^\\s\\\"<>]+',r'\\1[OWN-TOKEN]',raw)\nraw=re.sub(r'(https?",1)
p.write_text(s)
(H/'browser_queue.py').write_text('''import json,subprocess,sys
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[2];done=[]
for script in json.loads((H/'browser-queue.json').read_text()):
 p=subprocess.run([str(R/'.venv/bin/python'),str(H/'browser_run.py'),script],cwd=R)
 f=H/(script+'.result.json');d=json.loads(f.read_text())if f.exists()else{};rows=d.get('rows',[])
 receipt={'script':script,'exit':p.returncode,'rows':len(rows),'counts':{s:sum(r.get('status')==s for r in rows)for s in ['PASS','FAIL','NOT RUN']},'error':d.get('error')};done.append(receipt);(H/'queue-status.json').write_text(json.dumps(done,indent=2));print(json.dumps(receipt),flush=True)
 if p.returncode or not rows or d.get('error'):sys.exit(1)
 # Independent audit scripts continue on semantic FAIL/NOT RUN; findings remain explicit.
''')
print(json.dumps({'scripts':len(queue),'source':'historical module07 checklist adapted to current own Linux profile; assertions preserved or made concrete for accepted repairs','application_changes':[]}))
