from pathlib import Path
R=Path('/mnt/c/kidsmap');O=R/'docs/qa/site-qa22-recheck-2026-10-18-pc-r1'
s=(O/'browser-destination-prototype.js').read_text();start=s.index('// Labelled transport');end=s.index("await p.goto(base+'/qa/site08/login/super/');",start)
s=s[:start]+'''// PLAN simulation: the clicked browser form POST is forwarded by route.fetch
// (maxRedirects0), then only its response Location is replaced. This is a
// transport prototype, not a native unmodified redirect or applied-source GREEN.
await p.route('**/admin/catalog/sitefootersettings/1/change/',async r=>{if(r.request().method()!=='POST')return r.continue();const response=await r.fetch({maxRedirects:0});if(response.status()!==302)return r.fulfill({response});transport_rewrites.push({path:new URL(r.request().url()).pathname,method:'POST',forwarded_upstream_status:response.status(),upstream_location:response.headers().location,simulated_location:'/admin/catalog/sitesettings/'});return r.fulfill({response,headers:{...response.headers(),location:base+'/admin/catalog/sitesettings/'}});});
'''+s[end:]
s=s.replace('/png/destination-', '/png/destination-v2-').replace("native_POST302:status===302,email_saved", "forwarded_POST302:status===302,email_saved")
s=s.replace('PLAN ONLY: real native saves, simulated subsequent changelist GET302 destination, temporary CSS prototype with exact rollback. No application patch/no actual-source candidate GREEN. Source/backend RED is separate; this probes UI impact of the proposed destination.', 'PLAN ONLY: branding/restore native POSTs; clicked footer POST forwarded through route.fetch and Location replaced for destination preview. Temporary CSS prototype/exact rollback. Not unmodified native redirect, not applied-source GREEN. Previous v1 redirect intercept did not run and12actual_hub_render checks failed; retained.')
(O/'browser-destination-prototype-v2.js').write_text(s)
