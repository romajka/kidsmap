"""Strict verification of executed browser evidence and actual runtime source."""
import hashlib,json,sys
from collections import Counter
from pathlib import Path
root=Path(sys.argv[1]);out=Path(sys.argv[2])
d=json.loads((root/'results.json').read_text())
manifest=json.loads((root/'source-sha256.json').read_text())
current=json.loads((root/'source-current-check.json').read_text())
run=json.loads((root/'launcher/run.json').read_text())
isolation=json.loads((root/'launcher/isolation.json').read_text())
assert d['total']==d['passed']==273
assert len({(r['screen'],r['lang'],r['width'])for r in d['rows']})==273
assert all(not r['issues']for r in d['rows']) and all(c['pass']for c in d['checks'])
counts=Counter(c['check']for c in d['checks'])
assert counts['focus']==counts['tab']==273
for check in ('mode_keeps_filters_whole_month','same_month_calendar_paginated_list','calendar_back_keeps_selection','calendar_forward_list','calendar_reload_month_and_day','native_day_keyboard_focus','selected_mobile_day_and_multiday','quick_chip_keeps_all_filters','quick_period_full_HTTP','physical_filter_same_month','cancel_reschedule_same_event_ids','free_chip_retains_period_format_filters','month_keeps_all_filters','next_month_zero_state_actual','month_back_keeps_physical_filter'):
 assert counts[check]==21,check
assert counts['actual_list_period_form']==counts['list_period_keeps_filter_values']==6
assert counts['selected_day_AZ_fallback_marker']==21
assert counts['multiday_same_id_included']==3 and counts['multiday_end_exclusive']==1
assert len(d['checks'])==d['checksPassed']==924
assert not any(d['events'][k]for k in ('errors','failed','staticFailures'))
assert not current['mismatches'] and not current['new_application_files']
assert run['status']==run['cleanup']=='PASS' and run['run_root_removed'] and run['socket_root_removed']
assert isolation['django_testing'] and isolation['network_guard'] and isolation['libpq_guard'] and not isolation['external_credentials_present']
assert all('/root/km27-browser-frozen' in value for value in d['runtime'].values())
assets={}
for path,asset in d['runtimeAssets'].items():
 sha=hashlib.sha256(asset['text'].encode()).hexdigest()
 assert asset['status']==200 and sha==manifest[path],path
 assets[path]=sha
admincss='static/admin/css/pages/kidsmap_admin_form_shell.css'
assert hashlib.sha256(d['runtimeCss'].encode()).hexdigest()==manifest[admincss]
summary={'stage':27,'status':'PASS','execution_identity':'/root/stage26_browser','role':'browser-qa',
 'head':'015d031d8eb17114bd860159dde805b38df3c13c','snapshot':'dirty WORKTREE frozen in own allowlisted mirror',
 'evidence':str(root),'contexts':273,'passed_contexts':273,'checks':924,'passed_checks':924,
 'focus_tab_checks':546,'languages':['az','ru','en'],'widths':[320,360,390,768,1024,1280,1440],
 'check_counts':dict(counts),'runtime_paths':d['runtime'],'runtime_assets_sha256':assets,
 'admin_css_received_sha256':manifest[admincss],'source_current_check':current,
 'errors':0,'request_failures':0,'static_failures':0,'overflow_contexts':0,'cleanup':'PASS',
 'feature_contract':'Existing SiteSettings.events_section_enabled, synthetic local ON/OFF410/restoredON only; no global flag change',
 'external_transport':d['externalTransport'],
 'not_run':['Production','Real external integrations/CDNs','Physical devices/full screen-reader audit','Full application suite by this browser executor','Stage28','Deploy/commit/push']}
out.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({key:summary[key]for key in ('status','contexts','checks','focus_tab_checks','runtime_assets_sha256')}))
