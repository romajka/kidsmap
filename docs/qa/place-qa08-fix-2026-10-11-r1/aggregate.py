"""Aggregate final browser rows and render DERIVED QA contact sheets."""
import csv
import hashlib
import json
from pathlib import Path
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent
rows=[]
browser=[]
for name in ('placeholder-matrix','roundtrip'):
    data=json.loads((HERE/(name+'.result.json')).read_text(encoding='utf-8'))
    assert not data.get('error'), data.get('error')
    rows.extend(data['rows'])
    browser.append({'script':name,'pageerrors':[e for e in data['consoleErrors'] if e['type']=='pageerror'],'console_error_count':len(data['consoleErrors']),'local_http_errors':data['networkErrors'],'blocked':data['blocked']})
assert len(rows)==87
assert all(r['status']=='PASS' for r in rows)
assert all(not b['pageerrors'] and not b['local_http_errors'] for b in browser)
with (HERE/'matrix.csv').open('w',encoding='utf-8-sig',newline='') as stream:
    writer=csv.DictWriter(stream,fieldnames=['scenario','status','role','lang','width','url','shot','detail'])
    writer.writeheader()
    for row in rows:
        small={k:row.get(k,'') for k in writer.fieldnames if k!='detail'}
        small['detail']=json.dumps({k:v for k,v in row.items() if k not in small},ensure_ascii=False)
        writer.writerow(small)
manifest=[]
for path in sorted((HERE/'screenshots').glob('*.png')):
    with Image.open(path) as img: size=img.size
    manifest.append({'file':path.relative_to(HERE).as_posix(),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'width':size[0],'height':size[1],'kind':'NATIVE browser PNG'})
(HERE/'screenshots-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
for language in ('ru','az','en'):
    canvas=Image.new('RGB',(1500,1400),'#ffffff')
    draw=ImageDraw.Draw(canvas)
    for index,width in enumerate((360,390,768,1024,1280,1440)):
        x=(index%3)*500;y=(index//3)*700
        path=HERE/'screenshots'/f'district-empty-{language}-{width}.png'
        with Image.open(path) as img:
            copy=img.copy();copy.thumbnail((490,640));canvas.paste(copy,(x+(500-copy.width)//2,y+35))
        draw.text((x+15,y+10),f'DERIVED full viewport {language.upper()} {width}px',fill='#111111')
    canvas.save(HERE/f'contact-{language}.jpg',quality=92)
    # Separate crops make the district labels legible at every width.
    labels=Image.new('RGB',(1000,900),'#ffffff');labeldraw=ImageDraw.Draw(labels)
    for index,width in enumerate((360,390,768,1024,1280,1440)):
        x=(index%2)*500;y=(index//2)*300
        row=next(r for r in rows if r['lang']==language and r['width']==width and r['scenario']=='Empty district label visible and focused within viewport')
        g=row['geometry']
        with Image.open(HERE/row['shot']) as img:
            crop=img.crop((max(0,int(g['left'])-8),max(0,int(g['top'])-60),min(width,int(g['right'])+8),min(950,int(g['bottom'])+130)))
            crop.thumbnail((490,250));labels.paste(crop,(x+(500-crop.width)//2,y+35))
        labeldraw.text((x+10,y+10),f'DERIVED district crop {language.upper()} {width}px',fill='#111111')
    labels.save(HERE/f'labels-{language}.jpg',quality=95)
counts={'django_green':{'passed':6,'exit_code':0},'django_red_confirmed':{'tests':2,'failures':1,'ru_expected_failure':True,'exit_code':1},'browser':{s:sum(r['status']==s for r in rows) for s in ('PASS','FAIL','NOT RUN')},'browser_rows':len(rows),'native_png':len(manifest),'derived_contact_sheets':6,'full_module01':'NOT RUN','browser_diagnostics':browser}
(HERE/'counts.json').write_text(json.dumps(counts,indent=2),encoding='utf-8')
print('Final browser observations:',len(rows),'PASS; native PNG:',len(manifest),'DERIVED contacts: 6')
