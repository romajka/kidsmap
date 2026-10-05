"""Safe runtime CSS/source diagnosis; synthetic raw DOM stays outside Git."""
import hashlib,json,sys
from pathlib import Path
root=Path(sys.argv[1])
d=json.loads((root/'result-cli.txt').read_text().split('### Result',1)[1].split('###',1)[0])
css=d.pop('receivedCss')
(root/'runtime-results.json').write_text(json.dumps(d,ensure_ascii=False,indent=2))
run=json.loads((root/'launcher/run.json').read_text())
summary={'stage':26,'scope':'runtime CSS causal diagnosis','evidence':str(root),
 'received_css_sha256':hashlib.sha256(css.encode()).hexdigest(),
 'runtime_paths':d.get('runtime'),'computed':d['observed']['computed'],
 'document_scroll_width':d['observed']['scroll'],
 'forced_track_scroll_width':d['forced']['scroll'],
 'after_actual_admin_save':d['afterSave'],
 'cleanup':run['cleanup'],'launcher_status':run['status']}
print(json.dumps(summary,ensure_ascii=False))
