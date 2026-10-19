from pathlib import Path
O=Path(__file__).resolve().parent;F=O.parent/'site-qa21-fix-2026-10-18-pc-r1'
def adapt(s):
 for a,b in [('33560','33580'),('site-qa21-fix-2026-10-18-pc-r1','site-qa08-fix-2026-10-18-pc-r1'),('site21-pc-fix-r1','site08-pc-fix-r1'),('qa/site21/','qa/site08/')]:s=s.replace(a,b)
 return s
s=adapt((F/'browser-json-flows.js').read_text());s=s.replace("['super','editor']","['editor']").replace("for(const lang of ['az','ru','en']){","for(const lang of ['az','ru','en'])for(const width of [360,390]){await p.setViewportSize({width,height:1000});").replace('width:1440,action','width,action').replace('width:1440,field','width,field').replace("role+'-'+lang+'-'","role+'-'+lang+'-'+width+'-'").replace('Actual desktop textarea','Actual native mobile textarea')
(O/'browser-json-mobile.js').write_text(s)
(O/'browser-long-json.js').write_text(adapt((F/'browser-long-json.js').read_text()))
print('Proven JSON flows adapted to native360/390 for3locales; original-long fixture restoration retained.')
