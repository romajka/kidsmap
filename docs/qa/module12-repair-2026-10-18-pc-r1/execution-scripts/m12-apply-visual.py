import sys
sys.path.insert(0,'/mnt/c/kidsmap/.tmp/m12-full-r1')
from stage_apply import *
S=O/'stages/visual'
(S/'IMPLEMENTATION_PLAN.md').write_text('''# Dashboard native visual followup

User authorized newly found related defects. Native RED:60observations,0errors from current real DOM/computed styles and saved PNG. Original disabled report functional state now passes; UI followup fixes low-contrast active controls/status, a280px notice caused by reusing chart-empty, and actual KPI label/icon clipping at360 and1440. These are not hidden or dismissed as browser harness failures.

Exactly two files: templates/admin/catalog/site_analytics.html reuses existing compact km-ga4-notice and km-ga4-notice__text instead of chart-empty, keeping role=status/retry and all text; bumps CSS version. static/admin/css/kidsmap_statistics.css changes scoped brand green to existing KidsMap#136F38, muted text to readable existing gray,3-column minmax grid matching actual3cards,1column≤480, header gap/min-width/wrapping. No global public UI/JS/schema/data change. Existing stats CSS is used only by this dashboard.

Acceptance: actual18cells/3languages/six widths in each disabled/filled/empty/error/partial state; contrasts≥4.5, notice≤120px, content geometry without clipping, no document overflow; keyboard period/retry/focus and old targeted backend regressions unchanged. No runtime style injection. Preserve initial failed outputs and screenshots.
''')
files={}
p='templates/admin/catalog/site_analytics.html';text=(R/p).read_bytes().decode();text=text.replace('?v=20261018_site24_r1','?v=20261019_module12_r1');old='<div class="km-chart-empty" role="status">';assert old in text;text=text.replace(old,'<div class="km-ga4-notice" role="status">');old='{% if ga_reporting_state == "disabled" %}{% trans "GA4 не настроен." %}{% else %}{% trans "Данные GA4 временно недоступны." %}{% endif %}';assert old in text;text=text.replace(old,'<span class="km-ga4-notice__text">'+old+'</span>');files[p]=text.encode()
p='static/admin/css/kidsmap_statistics.css';text=(R/p).read_bytes().decode();assert '--km-s-green:      #009A4E;' in text;text=text.replace('--km-s-green:      #009A4E;','--km-s-green:      #136F38;');text=text.replace('color: #9CA3AF;','color: var(--km-s-gray);');text=text.replace('grid-template-columns: repeat(6, 1fr);','grid-template-columns: repeat(3, minmax(0, 1fr));')
nl='\r\n' if '\r\n' in text else '\n';text+=nl+'''/* Module12: keep actual KPI content readable at narrow dashboard widths. */
.km-statistics-page .km-kpi-card__header { gap: 8px; }
.km-statistics-page .km-kpi-card__label { min-width: 0; overflow-wrap: anywhere; }
@media (max-width: 480px) {
  .km-statistics-page .km-statistics-kpis { grid-template-columns: minmax(0, 1fr); }
}
'''.replace('\n',nl);files[p]=text.encode();apply('visual',files,'stages/visual/evidence/red-r1.json')
