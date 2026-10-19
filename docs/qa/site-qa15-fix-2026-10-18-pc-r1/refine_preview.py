import hashlib,json,re,subprocess,sys
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=Path(__file__).resolve().parent;Q=R/'.tmp/site15-pc-fix-r1'
def replace(rel,old,new):
 p=R/rel;b=p.read_bytes();s=b.decode().replace('\r\n','\n');assert old in s
 p.write_bytes(s.replace(old,new,1).replace('\n','\r\n').encode() if b'\r\n' in b else s.replace(old,new,1).encode())
 data=json.loads((Q/'expected-source.json').read_text());data['sources'][rel]=hashlib.sha256(p.read_bytes()).hexdigest();(Q/'expected-source.json').write_text(json.dumps(data,indent=2))
if sys.argv[1]=='red':
 rel='src/catalog/testcases/test_site_qa15_settings_concurrency.py';(O/'test-initial-candidate.py').write_bytes((R/rel).read_bytes())
 method='''    def test_stale_upload_preview_uses_current_stored_file(self):
        url = reverse('admin:catalog_sitebrandingsettings_change', args=[self.site.pk])
        self.site.logo = self.image()
        self.site.save()
        stored_name = self.site.logo.name
        data = self.payload(url)
        self.first_save()
        data['logo'] = self.image()
        response = self.assert_conflict(data, url)
        self.assertEqual(response.context['original'].logo.name, stored_name)

'''
 replace(rel,'    def test_draft_html_is_escaped_in_conflict_response(self):',method+'    def test_draft_html_is_escaped_in_conflict_response(self):')
 cmd=['docker','exec','m10s15-fix-r1-app','python',str(Q/'runtime.py'),'test','catalog.testcases.test_site_qa15_settings_concurrency.Site15SettingsConflictTests.test_stale_upload_preview_uses_current_stored_file']
 r=subprocess.run(cmd,capture_output=True,text=True);raw=r.stdout+r.stderr;(Q/'preview-red.log').write_text(raw)
 out={'command':cmd,'exit':r.returncode,'failures':len(re.findall('^FAIL:',raw,re.M)),'errors':len(re.findall('^ERROR:',raw,re.M)),'summary':[x for x in raw.splitlines() if x.startswith(('Ran ','FAILED (','OK'))],'raw_sha256':hashlib.sha256(raw.encode()).hexdigest()};(O/'evidence/preview-red.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2));assert out['exit']==1 and out['failures']==1 and out['errors']==0
elif sys.argv[1]=='apply':
 assert json.loads((O/'evidence/preview-red.json').read_text())['failures']==1
 rel='src/catalog/domain_admin/site.py';(O/'backend-initial-candidate.py').write_bytes((R/rel).read_bytes())
 replace(rel,'\n\nclass _SiteSettingsConcurrencyAdminMixin:', '''

    def _post_clean(self):
        # A rejected snapshot must not turn uncommitted uploads into preview URLs.
        if not getattr(self, "settings_conflict", False):
            super()._post_clean()


class _SiteSettingsConcurrencyAdminMixin:''')
 (O/'preview-refinement.json').write_text(json.dumps({'scope':'Approved backend and new regression file only','reason':'ModelForm._post_clean constructed the rejected file on the in-memory instance; readonly preview referenced an unsaved URL despite no storage write. Skip instance construction/model validation on already rejected conflict; bound text/checkbox widgets and notice still render submitted values. Fresh/other-invalid forms retain normal _post_clean.','regression_red':'evidence/preview-red.json','before_backend_sha256':hashlib.sha256((O/'backend-initial-candidate.py').read_bytes()).hexdigest(),'after_backend_sha256':hashlib.sha256((R/rel).read_bytes()).hexdigest()},indent=2));print('Conflict-only preview refinement applied; test now22methods')
