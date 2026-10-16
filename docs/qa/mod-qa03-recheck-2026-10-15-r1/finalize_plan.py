import json,hashlib,difflib,collections,struct
from pathlib import Path
H=Path(__file__).resolve().parent;ROOT=H.parents[2]
def read(n):return json.loads((H/n).read_text())
def save(n,d):(H/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def sha(b):return hashlib.sha256(b).hexdigest()
r=read('native-baseline-r2.js.result.json');s=read('native-stable-subset.js.result.json')
def match(x):return all(x.get(k)==v for k,v in dict(lang='en',model='place',width=1440,sidebar='collapsed',menu='base').items())
old=[x for x in r['rows']if match(x)];new=[x for x in s['rows']if match(x)]
assert len(old)==len(new)==6 and [x['id']for x in old]==[x['id']for x in new]
rows=[x for x in r['rows']if not match(x)]+new
counts=dict(collections.Counter(x['status']for x in rows));assert counts=={'PASS':1037,'FAIL':84}
save('accepted-baseline.json',{'mode':'Fresh unpatched baseline; confirmed source failures remain OPEN','sources':['native-baseline-r2.js.result.json','native-stable-subset.js.result.json'],'replacement':'Only six base observations EN/Place/1440/collapsed replaced after waiting for sidebar final72px. Raw results retained; same assertions. No implementation GREEN.','excluded_raw_rows':old,'replacement_rows':new,'counts':counts,'failure_groups':dict(collections.Counter(x['id']for x in rows if x['status']=='FAIL')),'rows':rows,'boundary':r['boundary']})
a=read('native-selected-trial-r2.js.result.json');b=read('native-shared-trial.js.result.json')
assert len(a['states'])==len(b['states'])==30
assert a['before']==a['after']==b['before']==b['after']
assert all(x['actual_lang']==x['lang'] and x['geometry']['root']<=x['width']+1 and all(y['updated']['width']>=100 and y['height']<150 for y in x['geometry']['rows']) and (x['wheel']is None or x['wheel']['local_scroll_left']>0 and x['wheel']['page_scroll_left']==0) for x in a['states'])
assert all(x['actual_lang']==x['lang'] and (x['root']<=x['width']+1 and x['panel']['left']>=0 and x['panel']['right']<=x['width']+1 and x['focus']['focus_visible'] and x['focus']['outline_width']=='2px' if x['kind']=='mobile-sort' else x['scroll']['left']>0 and x['scroll']['page_scroll_left']==0 and x['scroll']['root']<=x['width']+1) for x in b['states'])
save('simulated-design-summary.json',{'status':'SIMULATED ONLY; no source changes; not approved implementation or postpatch GREEN','chosen':'A: fixed layout retained, table min1000, updated header140, scoped local scroll and mobile sort left alignment','place_states':30,'native_place_scroll_states':21,'shared_mobile_keyboard_sort_states':18,'event_specialist_scroll_states':12,'same_synthetic_data':True,'source_results':['native-selected-trial-r2.js.result.json','native-shared-trial.js.result.json'],'alternative_B_C':'Not chosen: auto layout made RU1024 table1440.81px vs A1000px, no additional source scope needed.'})
file='static/admin/css/pages/kidsmap_changelist.css';original=(ROOT/file).read_bytes()
append='''\n/* MOD-QA-03: keep wide queue tables accessible inside their own viewport. */
.app-catalog.model-place .card-body.table-responsive,
.km-event-changelist .card-body.table-responsive,
.km-specialist-changelist .card-body.table-responsive {
    overflow-x: auto !important;
    overflow-y: hidden !important;
}

/* Preserve the updated/created column beside the expanded admin sidebar. */
.app-catalog.model-place .km-table-container #result_list {
    min-width: 1000px !important;
}

.app-catalog.model-place .km-table-container th.column-col_updated {
    width: 140px !important;
}

/* Narrow sort summaries must not anchor their wider panels off-screen. */
@media (max-width: 580px) {
    .app-catalog.model-place .km-sort-dropdown,
    .km-event-changelist .km-sort-dropdown,
    .km-specialist-changelist .km-sort-dropdown {
        left: 0;
        right: auto;
    }
}
'''
proposal=original+append.encode();(H/'proposed-kidsmap_changelist.css').write_bytes(proposal)
(H/'proposed.diff').write_text(''.join(difflib.unified_diff(original.decode().splitlines(True),proposal.decode().splitlines(True),fromfile='a/'+file,tofile='b/'+file)))
save('proposal-manifest.json',{'applied':False,'application_files':[file],'original_sha256':sha(original),'proposed_sha256':sha(proposal),'original_bytes_preserved_as_prefix':True,'append_lines':len(append.splitlines()),'scope_id':'MOD-QA-03'})
png=[]
for p in sorted((H/'screenshots').glob('*.png')):
 raw=p.read_bytes();w,h=struct.unpack('>II',raw[16:24]);n=p.name
 group='SIMULATED'if n.startswith(('trial-','selected-trial-','shared-trial-'))else 'BASELINE_R2'if n.startswith('baseline-r2-')else 'STABLE_SUBSET'if n.startswith('baseline-stable-subset-')else 'PARTIAL_BASELINE'if n.startswith('baseline-')else 'INSPECT'
 png.append({'path':str(p.relative_to(ROOT)),'sha256':sha(raw),'width':w,'height':h,'group':group})
save('png-manifest.json',{'count':len(png),'groups':dict(collections.Counter(x['group']for x in png)),'files':png})
save('visual-review.json',{'method':'manual image viewing via view_image; geometry/native events separate','images':['inspect-ru-place-1024-initial.png','baseline-r2-place-az-390-collapsed-sort.png','shared-trial-place-az-390-sort.png','selected-trial-r2-A-ru-1024-expanded.png'],'observations':'Baseline tall Place rows and clipped mobile sort visible. Browser-only simulation gives compact rows and on-screen AZ390 sort with keyboard focus outline. Not a visual review of every PNG or postpatch acceptance.'})
print(json.dumps({'baseline':counts,'png':len(png),'png_groups':dict(collections.Counter(x['group']for x in png)),'proposal_lines':len(append.splitlines())}))
