from pathlib import Path
Q=Path(__file__).resolve().parent
p=Q/'cell-body.js';t=p.read_text();t=t.replace('errors=[],failed=[],http=[]','errors=[],failed=[],http=[],consoleErrors=[]')
t=t.replace("page.on('pageerror',onError)","const onConsole=m=>{if(m.type()==='error')consoleErrors.push({text:m.text(),url:m.location().url});};page.on('console',onConsole);page.on('pageerror',onError)",1)
t=t.replace("owner.on('pageerror',onError)","owner.on('console',onConsole);owner.on('pageerror',onError)")
t=t.replace("const after=await state(),body=", "const denialURL=page.url();const denialFits=await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1);const after=await state(),body=")
t=t.replace("const recovery=await page.goto(o+prefix+'/account/notifications/');const reload=await page.reload();await finite();", "const recoveryLink=page.locator('a[href=\"'+prefix+'/account/notifications/\"]').first();await recoveryLink.scrollIntoViewIfNeeded();await recoveryLink.focus();const recoveryFocused=await recoveryLink.evaluate(e=>document.activeElement===e);const [recovery]=await Promise.all([page.waitForResponse(r=>r.url()===o+prefix+'/account/notifications/'&&r.request().method()==='GET'),recoveryLink.press('Enter')]);await page.waitForURL(o+prefix+'/account/notifications/');const reload=await page.reload();await finite();controls.denial_document_fits=denialFits;controls.denial_html_nonempty=Number(denial.headers()['content-length'])>0&&denialURL===o+acceptPath;controls.recovery_link_keyboard=recoveryFocused;")
t=t.replace("rendered_url:page.url()", "denial_url:denialURL,recovery_url:page.url()")
t=t.replace('pageerrors:errors,request_failed:failed,http_failures:http','pageerrors:errors,request_failed:failed,http_failures:http,consoleErrors')
t=t.replace("page.off('pageerror',onError)","page.off('console',onConsole);page.off('pageerror',onError)")
p.write_text(t)
p=Q/'matrix.py';t=p.read_text();t=t.replace("assert all(row['controls'].values()),row['controls']", "assert all(row['controls'].values()) and all(row['source'].values()),(row['controls'],row['source'])")
t=t.replace("assert all(f['url'].endswith('/accept/') and f['error']=='net::ERR_HTTP_RESPONSE_CODE_FAILURE' and row['facts']['response_body_length']==0 for f in row['request_failed']),row['request_failed']", "assert not row['request_failed'],row['request_failed']\n assert all(c['url'].endswith('/accept/') and '403' in c['text'] for c in row['consoleErrors']),row['consoleErrors']")
p.write_text(t)
# New own fixture helper extends only own fictional normal DB, never reseeds old data.
(Q/'fixtures.py').write_text('''from django.contrib.auth import get_user_model

def seed():
 U=get_user_model();assert not U.objects.filter(username='s08-fix-outsider').exists();U.objects.create_user('s08-fix-outsider',email='outsider-fix@example.invalid');print('Own outsider fictional guard user created')
''')
p=Q/'qa_urls.py';t=p.read_text().replace('get_user_model,login','get_user_model,login,logout').replace("role in ('owner','recipient')","role in ('owner','recipient','outsider','guest')")
t=t.replace("login(request,get_user_model().objects.get(username=case(key)[role]),backend='django.contrib.auth.backends.ModelBackend')", "if role=='guest':logout(request)\n else:login(request,get_user_model().objects.get(username='s08-fix-outsider' if role=='outsider' else case(key)[role]),backend='django.contrib.auth.backends.ModelBackend')")
p.write_text(t)
(Q/'tests.sh').write_text('''#!/bin/sh
set -u
qa=/mnt/c/kidsmap/.tmp/social08-pc-fix-r1
docker exec m09s08-fix-r1-app python "$qa/runtime.py" test catalog.testcases.test_social_qa08_invitation_feedback.SocialQA08InvitationFeedbackTests catalog.testcases.test_task33_notifications.WorkflowIntegrationTests.test_invitation_inbox_post_only_recipient_scoped_and_revocation_suppresses_mail catalog.testcases.test_task33_notifications.WorkflowIntegrationTests.test_changed_email_cannot_read_old_address_notification catalog.testcases.test_task33_notifications.WorkflowIntegrationTests.test_csrf_required_for_inbox_actions > "$qa/tests.log" 2>&1
result=$?
printf '%s\\n' "$result" > "$qa/tests.exit"
tail -n 10 "$qa/tests.log"
exit "$result"
''')
(Q/'start-app.sh').write_text('''#!/bin/sh
set -eu
qa=/mnt/c/kidsmap/.tmp/social08-pc-fix-r1
docker exec m09s08-fix-r1-app python "$qa/runtime.py" seed > "$qa/seed.log" 2>&1
docker exec -d m09s08-fix-r1-app sh -c 'python /mnt/c/kidsmap/.tmp/social08-pc-fix-r1/runtime.py serve > /mnt/c/kidsmap/.tmp/social08-pc-fix-r1/server.log 2>&1'
''')
print('Native RED assertions preserved; GREEN adds actual recovery keyboard/HTML/layout/full console capture; targeted12test labels')
