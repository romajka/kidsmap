import sys,json,re,ast
sys.path.insert(0,'/mnt/c/kidsmap/.tmp/m12-full-r1')
from stage_apply import *
S=O/'stages/reporting'
(S/'IMPLEMENTATION_PLAN.md').write_text('''# Reporting/localization — exact approved scope

Historical04/05/06/08 freshly reproduced against current sources/current isolated MO. REDr3:10methods/22failure observations/0errors. One overview translation already correct; retain it. Existing 7/30/365 windows and labelled fixed30-day charts/tables remain unchanged.

Files: services/google_analytics_reporting.py adds quarter=89daysAgo in empty stats and PERIODS; services/admin_analytics.py selects quarter for90, treats unavailable/missing selected period as None, gates partial chart/top arrays, records load time only when connected and selected stats present, and uses a truthful unavailable-comparison label independent of local storage. templates/admin/catalog/site_analytics.html declares state, shows accessible generic status/retry, real successful load timestamp or not-loaded label. src/catalog/templates/pages/owner_analytics.html adds AZ comparison branch. locale AZ changes only14 specific erroneous analytics messages (15checked,1already correct), plus five new messages in AZ/RU/EN. Add two exact fresh-red candidate regression modules.

Consumer state: disabled when identifiers absent; unavailable on failure/partial/missing selected window; ready on confirmed complete report. Unavailable KPI values None with em dash, no false zero/updated label/provider error leakage. Ready successful empty stays0. Existing empty table wording retained under explicit status. Normal link retries same selected period. No real GA transport/property/config or schema change. Native allstates/roles/periods/keyboard/three languages/six widths after fresh current-source backend GREEN.
''')
files={}
def change(path,old,new,count=1):
 data=files.get(path,(R/path).read_bytes()).decode()
 if '\r\n' in data:old=old.replace('\r\n','\n').replace('\n','\r\n');new=new.replace('\r\n','\n').replace('\n','\r\n')
 assert data.count(old)==count,(path,old,data.count(old));files[path]=data.replace(old,new).encode()
p='src/catalog/services/google_analytics_reporting.py'
change(p,'        "month": dict(empty),','        "month": dict(empty),\n        "quarter": dict(empty),')
change(p,'        "month": "29daysAgo",','        "month": "29daysAgo",\n        "quarter": "89daysAgo",')
p='src/catalog/services/admin_analytics.py'
change(p,'Дельта недоступна в локальном режиме без хранения сырых событий','Сравнение с предыдущим периодом недоступно.')
change(p,'value: int, icon:','value: int | None, icon:')
change(p,'"value": int(value or 0),\n        "formatted_value": "",','"value": int(value) if value is not None else None,\n        "formatted_value": "" if value is not None else "—",')
change(p,'    return "year"\n','    if period_days <= 90:\n        return "quarter"\n    return "year"\n')
change(p,'    ga_stats = ga4.get("period_stats", {}).get(ga_period, {})','    ga_stats = ga4.get("period_stats", {}).get(ga_period, {})\n    ga_ready = bool(ga4.get("enabled") and ga4.get("connected") and ga_stats)\n    ga_state = "ready" if ga_ready else ("unavailable" if ga4.get("enabled") else "disabled")\n\n    def metric(name):\n        return int(ga_stats.get(name) or 0) if ga_ready else None')
for key in ['active_users','sessions','page_views']:change(p,'int(ga_stats.get("'+key+'") or 0)','metric("'+key+'")',count=2)
change(p,'    chart = ga4.get("daily_chart") or {}','    chart = (ga4.get("daily_chart") or {}) if ga_ready else {}')
change(p,'        "period_days": period_days,','        "ga_reporting_state": ga_state,\n        "ga4_loaded_at": timezone.now() if ga_ready else None,\n        "period_days": period_days,')
change(p,'"ga4_top_pages": list(ga4.get("top_pages") or []),','"ga4_top_pages": list(ga4.get("top_pages") or []) if ga_ready else [],')
change(p,'"ga4_top_events": list(ga4.get("top_events") or []),','"ga4_top_events": list(ga4.get("top_events") or []) if ga_ready else [],')
p='templates/admin/catalog/site_analytics.html'
change(p,'class="km-statistics-page">','class="km-statistics-page" data-analytics-state="{{ ga_reporting_state }}">')
change(p,'            <span>↻</span>\n            <span>{% trans "Обновлено сегодня" %}</span>','            <span aria-hidden="true">↻</span>\n            {% if ga4_loaded_at %}\n              <time datetime="{{ ga4_loaded_at|date:\'c\' }}">{% trans "Обновлено" %} {{ ga4_loaded_at|date:"d.m.Y H:i" }}</time>\n            {% else %}\n              <span>{% trans "Данные не загружены" %}</span>\n            {% endif %}')
change(p,'      <section class="km-statistics-kpis">','      {% if ga_reporting_state != "ready" %}\n        <div class="km-chart-empty" role="status">\n          {% if ga_reporting_state == "disabled" %}{% trans "GA4 не настроен." %}{% else %}{% trans "Данные GA4 временно недоступны." %}{% endif %}\n          {% if ga_reporting_state == "unavailable" %}<a class="km-period-selector__btn" href="?period={{ period_days }}">{% trans "Повторить загрузку" %}</a>{% endif %}\n        </div>\n      {% endif %}\n      <section class="km-statistics-kpis">')
p='src/catalog/templates/pages/owner_analytics.html'
change(p,'{% if CURRENT_LANGUAGE == "en" %}vs previous period{% else %}к прошлому периоду{% endif %}','{% if CURRENT_LANGUAGE == "az" %}əvvəlki dövrlə müqayisədə{% elif CURRENT_LANGUAGE == "en" %}vs previous period{% else %}к прошлому периоду{% endif %}',count=2)
tree=ast.parse((Q/'test_m12_localization_candidate.py').read_text());labels=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='AZ_LABELS' for t in n.targets))
new={
 'GA4 не настроен.':{'az':'GA4 konfiqurasiya edilməyib.','en':'GA4 is not configured.'},
 'Данные GA4 временно недоступны.':{'az':'GA4 məlumatları müvəqqəti olaraq əlçatan deyil.','en':'GA4 data is temporarily unavailable.'},
 'Повторить загрузку':{'az':'Yükləməni təkrarla','en':'Retry loading'},
 'Данные не загружены':{'az':'Məlumatlar yüklənməyib','en':'Data not loaded'},
 'Сравнение с предыдущим периодом недоступно.':{'az':'Əvvəlki dövrlə müqayisə əlçatan deyil.','en':'Comparison with the previous period is unavailable.'},
}
def update_po(text,source,target,allow_new=False):
 newline='\r\n' if '\r\n' in text else '\n';parts=re.split(r'(\r?\n\r?\n)',text);needle='msgid '+json.dumps(source,ensure_ascii=False);matches=[]
 for i,part in enumerate(parts):
  lines=part.splitlines()
  if needle not in lines:continue
  matches.append(i);start=next(j for j,line in enumerate(lines) if line.startswith('msgstr '));end=start+1
  while end<len(lines) and lines[end].startswith('"'):end+=1
  if lines[start:end]==['msgstr '+json.dumps(target,ensure_ascii=False)] and not any(line.startswith('#,') and 'fuzzy' in line for line in lines):continue
  lines[start:end]=['msgstr '+json.dumps(target,ensure_ascii=False)]
  cleaned=[]
  for line in lines:
   if line.startswith('#,'):
    flags=[f.strip() for f in line[2:].split(',') if f.strip()!='fuzzy'];line='#, '+', '.join(flags) if flags else ''
   if line:cleaned.append(line)
  parts[i]=newline.join(cleaned)
 assert len(matches)<=1,(source,len(matches))
 if not matches:
  assert allow_new,source
  return text+newline+newline+'# Module12 reporting state'+newline+needle+newline+'msgstr '+json.dumps(target,ensure_ascii=False)+newline
 return ''.join(parts)
for lang in ['az','ru','en']:
 p='locale/'+lang+'/LC_MESSAGES/django.po';text=(R/p).read_bytes().decode()
 if lang=='az':
  for source,target in labels.items():text=update_po(text,source,target)
 for source,targets in new.items():text=update_po(text,source,source if lang=='ru' else targets[lang],True)
 files[p]=text.encode()
files['src/catalog/testcases/test_module12_reporting.py']=(Q/'test_m12_reporting_candidate.py').read_bytes();files['src/catalog/testcases/test_module12_localization.py']=(Q/'test_m12_localization_candidate.py').read_bytes()
apply('reporting',files,'stages/reporting/evidence/red-r3.json')
