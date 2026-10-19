import json
from pathlib import Path
O=Path(__file__).resolve().parent;Q=O.parents[2]/'.tmp/site06-pc-plan-r1'
p=O/'candidate/src/catalog/testcases/test_site_qa06_media_validation.py'
(O/'test-initial-candidate.py').write_bytes(p.read_bytes());(O/'evidence/red-initial-backend.json').write_bytes((O/'evidence/red-backend.json').read_bytes());(Q/'red-initial-tests.log').write_bytes((Q/'red-tests.log').read_bytes())
s=p.read_text();assert s.count("        self.assertIn('")==3
s=s.replace("        self.assertIn('","        self.assertIsNotNone(response.context)\n        self.assertIn('")
method='''    def test_truncated_raster_after_a_real_header_is_rejected(self):
        for fmt, ext, mime in [('PNG', 'png', 'image/png'), ('JPEG', 'jpg', 'image/jpeg')]:
            with self.subTest(format=fmt):
                raw = self.raster(fmt, size=(32, 32), mode='RGB')
                self.reject(self.upload('truncated.' + ext, raw[:len(raw) // 2], mime))

'''
s=s.replace('    def test_empty_file_is_rejected_without_write(self):',method+'    def test_empty_file_is_rejected_without_write(self):')
p.write_text(s)
stage=json.loads((Q/'stage.json').read_text());stage['test_db']='test_m10s06_plan_r1_final';(Q/'stage.json').write_text(json.dumps(stage))
print('Original RED/candidate retained; form-context assertions now fail cleanly on unexpected302. Added real truncated PNG/JPEG test. Fresh final testDB selected; app unchanged.')
