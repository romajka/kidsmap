import hashlib,json,subprocess
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=Path(__file__).resolve().parent;Q=R/'.tmp/site06-pc-fix-r1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
P=R/'docs/qa/site-qa06-recheck-2026-10-18-pc-r1';manifest=json.loads((P/'candidate-manifest.json').read_text())
for rel,d in manifest['files'].items():
 assert sha(R/rel)==d['candidate_sha256'];dest=O/'initial-applied'/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((R/rel).read_bytes())
# The incomplete native run and all its PNGs stay immutable under their original names.
for name in ['browser-green-matrix.json','browser-green-matrix-cli.txt']:(O/'evidence'/('initial-'+name)).write_bytes((O/'evidence'/name).read_bytes())
p=R/'src/catalog/testcases/test_site_qa06_media_validation.py';raw=p.read_bytes();assert raw.endswith(b'\n')
addition='''
    def test_media_errors_are_visible_and_linked_to_each_file_input(self):
        for model, field in [('sitebrandingsettings', 'logo'), ('siteanalytics', 'logo'), ('sitegalleryimage', 'image')]:
            with self.subTest(model=model):
                url = reverse('admin:catalog_' + model + ('_add' if model == 'sitegalleryimage' else '_change'), args=[] if model == 'sitegalleryimage' else [self.site.pk])
                data = self.payload(url)
                if model == 'sitegalleryimage':
                    data['placement'] = 'HOME_HERO'
                data[field] = self.upload('broken.png', b'not a png')
                response = self.client.post(url, data)
                self.assertEqual(response.status_code, 200)
                html = response.content.decode()
                auto_id = 'id_' + field
                tag = re.search(r'<input(?=[^>]*name="' + field + r'")[^>]*>', html).group()
                self.assertIn('aria-describedby="' + auto_id + '_media_error"', tag)
                self.assertIn('id="' + auto_id + '_media_error"', html)
                self.assertIn('href="#' + auto_id + '"', html)
                self.assertIn('errorlist d-none', html)
'''
p.write_bytes(raw+addition.encode())
sources=json.loads((Q/'expected-source.json').read_text())['sources'];sources[p.relative_to(R).as_posix()]=sha(p);(Q/'expected-source.json').write_text(json.dumps({'sources':sources},indent=2))
(Q/'stage.json').write_text(json.dumps({'locales':'locales-green','test_db':'test_m10s06_fix_r1_refine_red'}))
subprocess.run(['docker','exec','m09full-r1-pg','createdb','-U','m09full_r1','-O','m09full_r1','test_m10s06_fix_r1_refine_red'],check=True)
cmd=['docker','exec','m10s06-fix-r1-app','python',str(Q/'runtime.py'),'test','catalog.testcases.test_site_qa06_media_validation.Site06MediaValidationTests.test_media_errors_are_visible_and_linked_to_each_file_input']
r=subprocess.run(cmd,capture_output=True,text=True);raw=r.stdout+r.stderr;(Q/'refinement-red.log').write_text(raw)
import re
d={'command':cmd,'exit':r.returncode,'failure_observations':len(re.findall('^FAIL:',raw,re.M)),'errors':len(re.findall('^ERROR:',raw,re.M)),'summary':[x for x in raw.splitlines() if x.startswith(('Ran ','FAILED (','OK'))],'raw_sha256':hashlib.sha256(raw.encode()).hexdigest()};(O/'evidence/refinement-red.json').write_text(json.dumps(d,indent=2));print(json.dumps(d,indent=2));assert r.returncode==1 and d['failure_observations']==3 and d['errors']==0
