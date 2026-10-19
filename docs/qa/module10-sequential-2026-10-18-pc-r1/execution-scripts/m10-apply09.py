import sys,json
sys.path.insert(0,'/mnt/c/kidsmap/.tmp/m10-seq-r1')
from stage_apply import *
n=json.loads((O/'evidence/browser-site09-baseline.json').read_text());assert len([r for r in n['rows'] if False in r['checks'].values()])==9 and n['initial']['enabled']==n['final']['enabled'] and n['initial']['entity_sha256']==n['final']['entity_sha256']
path='src/catalog/views.py';t=(R/path).read_bytes().decode();nl='\r\n' if '\r\n' in t else '\n'
old='from .services.features import require_events_section_enabled, require_specialists_section_enabled';assert t.count(old)==1;t=t.replace(old,'from .services.features import is_events_section_enabled, require_events_section_enabled, require_specialists_section_enabled')
for method in ['get_active_place_for_legacy_redirect','get_active_place_with_gallery']:
 old='    place = place_controller.'+method+'(pk=pk)'+nl
 # gallery method also belongs to engagement views: patch only the first direct-page occurrence.
 assert old in t;t=t.replace(old,old+'    if place.is_temporary and not is_events_section_enabled():'+nl+'        return HttpResponseGone()'+nl,1)
apply('09',{path:t.encode(),'src/catalog/testcases/test_site_qa09_legacy_events_switch.py':(Q/'test_site09_candidate.py').read_bytes()})
(O/'browser-site09-green.js').write_bytes((O/'browser-site09-baseline.js').read_bytes())
