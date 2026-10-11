"""Own local social-card approximation from captured native head; never external bots."""
import json,html
from pathlib import Path
P=Path(__file__).resolve().parent;out=P/'previews';out.mkdir(exist_ok=True)
x=json.loads((P/'post-change.result.txt').read_text(encoding='utf-8'));manifest=[]
for s in x['samples']:
 h=s['head'];name=s['kind']+'-'+s['lang'];esc=lambda v:html.escape(str(v or ''),quote=True)
 page='<!doctype html><html lang="'+s['lang']+'"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>SIMULATED local QA11 preview</title><style>body{font:16px system-ui;margin:24px;background:#f1f5f4;color:#14261c}h1{font-size:20px}article{max-width:650px;margin:24px auto;border:1px solid #b9cfc2;background:white;border-radius:18px;overflow:hidden}img{width:100%;height:230px;object-fit:contain;background:#dfece4}section{padding:18px}h2,p{overflow-wrap:anywhere}small{display:block;color:#456657}aside{max-width:650px;margin:20px auto;padding:16px;background:#e1ecf8}code{overflow-wrap:anywhere}</style><h1>SIMULATED · локальная QA-карточка по фактическим OG metadata</h1><p>Это собственный preview. Проверка внешней платформы и её бота NOT RUN.</p><article><img src="'+esc(h.get('ogImage'))+'" alt="Actual og:image"><section><small>localhost:8827</small><h2>'+esc(h.get('ogTitle'))+'</h2><p>'+esc(h.get('ogDescription'))+'</p></section></article><aside><strong>Публичная карточка</strong><p>H1: '+esc(h['h1'][0])+'</p><p>meta description: '+esc(h.get('description'))+'</p><code>'+esc(h.get('canonical'))+'</code></aside></html>'
 (out/(name+'.html')).write_text(page,encoding='utf-8');manifest.append({'name':name,'path':'previews/'+name+'.html','sourceURL':s['url'],'kind':s['kind'],'lang':s['lang']})
(P/'previews-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8');print('Local SIMULATED previews',len(manifest))
