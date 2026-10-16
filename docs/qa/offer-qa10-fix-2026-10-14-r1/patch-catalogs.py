import re,json
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[2]
ids=['Абонемент','Лагерь','Тур','Дополнительная услуга','Точная цена','Диапазон','По запросу','Год','Индивидуальный']
values={'az':['Abunə','Düşərgə','Tur','Əlavə xidmət','Dəqiq qiymət','Qiymət aralığı','Sorğu əsasında','İl','Fərdi'],'en':['Membership','Camp','Tour','Additional service','Exact price','Price range','On request','Year','Individual']}
for lang in ['az','en']:
 f=R/'locale'/lang/'LC_MESSAGES/django.po';raw=f.read_text();assert raw==(P/('incoming-'+lang+'.po')).read_text();parts=re.split('(\n\n)',raw);seen=[]
 for i,b in enumerate(parts):
  match=re.search(r'^msgid "([^"]+)"$',b,re.M)
  if not match or match.group(1) not in ids or re.search(r'^msgctxt ',b,re.M):continue
  key=match.group(1);seen.append(key)
  b=re.sub(r'^#, ([^\n]*)$',lambda m:('#, '+', '.join(x for x in m[1].split(', ') if x!='fuzzy')) if any(x!='fuzzy' for x in m[1].split(', ')) else '',b,flags=re.M)
  b=re.sub(r'^msgstr "[^\n]*"(?:\n"[^\n]*")*', 'msgstr '+json.dumps(values[lang][ids.index(key)],ensure_ascii=False),b,flags=re.M)
  parts[i]=b
 assert sorted(seen)==sorted(ids),seen
 f.write_text(''.join(parts))
print('18 scoped AZ/EN entries; RU identity entries already effective, unchanged')
