"""Render shared audit content as a portable HTML report and Markdown."""
import html,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
data=json.loads((ROOT/'report-data.json').read_text(encoding='utf8'))
def inline(value):
    value=html.escape(str(value))
    value=re.sub(r'`([^`]+)`',r'<code>\1</code>',value)
    value=re.sub(r'\*\*([^*]+)\*\*',r'<strong>\1</strong>',value)
    value=re.sub(r'\[([^]]+)\]\(([^)]+)\)',r'<a href="\2">\1</a>',value)
    return value
parts=[];md=['# '+data['title'],'',data['subtitle'],''];nav=[]
for i,section in enumerate(data['sections'],1):
    ident='section-'+str(i);nav.append(f'<a href="#{ident}">{inline(section["title"])}</a>')
    parts.append(f'<section id="{ident}"><h2>{inline(section["title"])}</h2>')
    md+=['## '+section['title'],'']
    for p in section.get('paragraphs',[]):parts.append('<p>'+inline(p)+'</p>');md += [p,'']
    for bullets in section.get('lists',[]):
        parts.append('<ul>'+''.join('<li>'+inline(x)+'</li>'for x in bullets)+'</ul>');md += ['- '+x for x in bullets]+['']
    for table in section.get('tables',[]):
        if table.get('title'):parts.append('<h3>'+inline(table['title'])+'</h3>');md += ['### '+table['title'],'']
        parts.append('<div class="table-scroll" tabindex="0" aria-label="Таблица: '+html.escape(table.get('title',section['title']))+'"><table><thead><tr>'+''.join('<th scope="col">'+inline(h)+'</th>'for h in table['headers'])+'</tr></thead><tbody>')
        md+=['| '+' | '.join(table['headers'])+' |','|'+'---|'*len(table['headers'])]
        for row in table['rows']:
            parts.append('<tr>'+''.join('<td>'+inline(cell)+'</td>'for cell in row)+'</tr>')
            md.append('| '+' | '.join(str(c).replace('|','/').replace('\n',' ')for c in row)+' |')
        parts.append('</tbody></table></div>');md.append('')
    if section.get('flows'):
        for flow in section['flows']:
            parts.append('<h3>'+inline(flow['title'])+'</h3><ol class="flow">'+''.join('<li>'+inline(s)+'</li>'for s in flow['steps'])+'</ol>')
            md+=['### '+flow['title'],'',' → '.join(flow['steps']),'']
    if section.get('gallery'):
        parts.append('<div class="gallery">')
        for item in section['gallery']:
            path=item['path'];caption=item['caption']
            parts.append('<figure><a href="'+html.escape(path)+'"><img loading="lazy" src="'+html.escape(path)+'" alt="'+html.escape(caption)+'"></a><figcaption>'+inline(caption)+'</figcaption></figure>')
            md+=['![Тестовый экран: '+caption.replace(']','')+']('+path+')','',caption,'']
        parts.append('</div>')
    parts.append('</section>')
requirements=json.loads((ROOT/'requirements-review.json').read_text(encoding='utf8'))['requirements']
reqhtml=[];reqmd=['# №33 — подробная сверка требований','',f'Всего: {len(requirements)}. Статус относится к фактическому доказательству, а не только к отметке DONE.','']
for item in requirements:
    title=f"{item['id']} · {item['status']}"
    text=item.get('text',item.get('requirement',''))
    evidence=item.get('evidence',[]);limits=item.get('limitations',[])
    if not isinstance(evidence,list):evidence=[evidence]
    if not isinstance(limits,list):limits=[limits]
    evidence=[json.dumps(x,ensure_ascii=False)if not isinstance(x,str)else x for x in evidence]
    limits=[json.dumps(x,ensure_ascii=False)if not isinstance(x,str)else x for x in limits]
    reqhtml.append('<details class="requirement"><summary>'+inline(title)+'</summary><p>'+inline(text)+'</p><p><b>Evidence:</b> '+inline('; '.join(evidence))+'</p><p><b>Границы:</b> '+inline('; '.join(limits)or'См. методику аудита.')+'</p></details>')
    reqmd+=['## '+title,'',text,'','Evidence: '+'; '.join(evidence),'','Границы: '+'; '.join(limits),'']
parts.append('<section id="requirements"><h2>Приложение: все306 требований</h2><p>Поиск по ID, этапу, формулировке и статусу. Раскройте строку для доказательств и ограничений.</p><label for="requirement-search">Найти требование</label><input id="requirement-search" type="search" placeholder="Например: R19, тариф, отзыв"><p id="requirement-count" role="status">306 требований</p>'+''.join(reqhtml)+'</section>')
nav.append('<a href="#requirements">Все306 требований</a>')
css='''
:root{--ink:#142b3b;--muted:#536472;--accent:#116861;--line:#dbe3e8;--paper:#fff;--bg:#f2f5f7}*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;color:var(--ink);background:var(--bg);font:16px/1.65 system-ui,-apple-system,"Segoe UI",sans-serif}a{color:#075e85;text-underline-offset:3px}a:focus-visible,summary:focus-visible,input:focus-visible,button:focus-visible,[tabindex]:focus-visible{outline:3px solid #c97914;outline-offset:3px}header{background:#102e40;color:white;padding:48px max(24px,calc((100vw - 1280px)/2));border-bottom:6px solid #26a28e}header p{max-width:920px;color:#d8e4ec}h1{font-size:clamp(28px,4vw,48px);line-height:1.18;margin:12px 0 20px;max-width:980px;letter-spacing:-.025em}h2{font-size:28px;line-height:1.28;margin:0 0 22px}h3{font-size:20px;margin:30px 0 14px}.eyebrow{text-transform:uppercase;letter-spacing:.12em;font-size:12px;font-weight:700}.layout{display:grid;grid-template-columns:235px minmax(0,1fr);gap:32px;max-width:1376px;margin:auto;padding:32px 24px}nav{position:sticky;top:18px;align-self:start;font-size:13px;max-height:94vh;overflow:auto}nav a{display:block;padding:7px 12px;border-left:2px solid var(--line);text-decoration:none;color:var(--muted)}nav a:hover{color:var(--accent);border-color:var(--accent)}main{min-width:0}section{background:var(--paper);border:1px solid var(--line);padding:34px;margin-bottom:24px;border-radius:8px;scroll-margin-top:20px}p{margin:0 0 17px}.table-scroll{overflow-x:auto;margin:18px 0 26px}table{border-collapse:collapse;width:100%;font-size:14px;line-height:1.5}th{text-align:left;background:#eaf0f3;font-size:12px;text-transform:uppercase;letter-spacing:.04em}td,th{padding:13px 15px;border-bottom:1px solid var(--line);vertical-align:top}td:first-child{font-weight:600}tr:nth-child(even){background:#f8fafb}td code{word-break:break-word}code{background:#eef3f5;padding:2px 4px;border-radius:3px;font:12px/1.5 ui-monospace,Consolas,monospace;overflow-wrap:anywhere}.flow{list-style:none;display:flex;flex-wrap:wrap;gap:12px;padding:0;counter-reset:step}.flow li{background:#eaf6f1;border-left:3px solid var(--accent);padding:13px 15px;flex:1 1 150px;font-size:14px}.flow li:before{counter-increment:step;content:counter(step)". ";font-weight:700;color:var(--accent)}.gallery{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:24px}.gallery figure{margin:0;border:1px solid var(--line);background:#f7f9fb}.gallery img{width:100%;height:340px;object-fit:contain;display:block;background:#e8eef2}.gallery figcaption{padding:16px;font-size:13px;line-height:1.55}details{border-bottom:1px solid var(--line);padding:12px 0}summary{cursor:pointer;font-weight:600;font-size:14px}details p{font-size:13px;margin:12px 0;overflow-wrap:anywhere}input{display:block;width:100%;max-width:520px;padding:12px;border:1px solid #aab8c2;border-radius:4px;font:inherit;margin:8px 0}button{font:inherit;background:#fff;color:#102e40;border:0;padding:10px 16px;border-radius:4px;cursor:pointer}.meta{font-size:13px}footer{text-align:center;padding:32px;color:var(--muted);font-size:13px}ul{padding-left:22px}li{margin-bottom:7px}[hidden]{display:none!important}
@media(max-width:900px){.layout{grid-template-columns:1fr;padding:20px 14px;gap:12px}nav{position:static;max-height:180px;border:1px solid var(--line);padding:10px;background:white}section{padding:24px 18px}h2{font-size:23px}.gallery{grid-template-columns:1fr}header{padding:32px 20px}td,th{padding:10px;min-width:110px}td:first-child{min-width:65px}.gallery img{height:360px}}
@media print{body{background:white;font-size:10pt}header{padding:18px;color:#142b3b;background:white;border-color:#116861}header p{color:#536472}header button,nav,#requirement-search,label[for=requirement-search],#requirement-count{display:none}.layout{display:block;max-width:none;padding:0}section{border:0;border-radius:0;padding:18px 0;break-before:auto}h1{font-size:26pt}h2{font-size:19pt}h3{font-size:14pt}table{font-size:8pt}.table-scroll{overflow:visible}td,th{padding:7px;min-width:0}tr,figure{break-inside:avoid}.gallery{grid-template-columns:repeat(2,minmax(0,1fr))}.gallery img{height:210px}.gallery figcaption{font-size:8pt}details{font-size:8pt}footer{padding:12px}@page{size:A4;margin:15mm}}
'''
script='''const input=document.getElementById('requirement-search');const rows=[...document.querySelectorAll('.requirement')];input.addEventListener('input',()=>{const q=input.value.toLocaleLowerCase('ru');let count=0;rows.forEach(row=>{row.hidden=!row.textContent.toLocaleLowerCase('ru').includes(q);if(!row.hidden)count++;});document.getElementById('requirement-count').textContent=count+' из '+rows.length+' требований';});document.getElementById('print-report').addEventListener('click',()=>window.print());'''
css+='\nbody{overflow-wrap:anywhere}summary{overflow-wrap:anywhere}.gallery img{object-fit:cover;object-position:top}\n'
htmltext='<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+html.escape(data['title'])+'</title><style>'+css+'</style></head><body><header><div class="eyebrow">KidsMap · №33 · аудит28 этапов · 4 октября2026</div><h1>'+inline(data['title'])+'</h1><p>'+inline(data['subtitle'])+'</p><p class="meta">'+inline(data['snapshot'])+'</p><button id="print-report" type="button">Печать / сохранить PDF</button></header><div class="layout"><nav aria-label="Содержание отчёта">'+''.join(nav)+'</nav><main>'+''.join(parts)+'</main></div><footer>Локальные синтетические данные · реальные browser screenshots · production не проверялся</footer><script>'+script+'</script></body></html>'
htmltext=htmltext.replace('аудит28','аудит 28').replace('октября2026','октября 2026').replace('Все306','Все 306').replace('все306','все 306')
(ROOT/'report.html').write_text(htmltext,encoding='utf8')
(ROOT/'REPORT.md').write_text('\n'.join(md)+'\n\n[Все306 требований](REQUIREMENTS.md) · [Интерактивный HTML-отчёт](report.html)\n',encoding='utf8')
(ROOT/'REQUIREMENTS.md').write_text('\n'.join(reqmd)+'\n',encoding='utf8')
print(json.dumps({'sections':len(data['sections']),'requirements':len(requirements),'html_bytes':len(htmltext.encode())}))
