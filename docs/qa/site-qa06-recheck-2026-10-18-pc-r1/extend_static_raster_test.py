import json
from pathlib import Path
O=Path(__file__).resolve().parent;Q=O.parents[2]/'.tmp/site06-pc-plan-r1';p=O/'candidate/src/catalog/testcases/test_site_qa06_media_validation.py'
(O/'test-v2-candidate.py').write_bytes(p.read_bytes());(O/'evidence/red-v2-backend.json').write_bytes((O/'evidence/red-backend.json').read_bytes());(Q/'red-v2-tests.log').write_bytes((Q/'red-tests.log').read_bytes())
s=p.read_text();method='''    def test_animated_png_is_rejected_by_static_media_policy(self):
        buffer = io.BytesIO()
        with Image.new('RGB', (16, 16), 'green') as first, Image.new('RGB', (16, 16), 'blue') as second:
            first.save(buffer, 'PNG', save_all=True, append_images=[second], duration=100)
        self.reject(self.upload('animated.png', buffer.getvalue()))

''';s=s.replace('    def test_empty_file_is_rejected_without_write(self):',method+'    def test_empty_file_is_rejected_without_write(self):');p.write_text(s)
stage=json.loads((Q/'stage.json').read_text());stage['test_db']='test_m10s06_plan_r1_static';(Q/'stage.json').write_text(json.dumps(stage));print('Static-raster policy regression added before candidate backend; original83method RED retained; new testDB selected')
