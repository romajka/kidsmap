"""Read actual active Django translations and compare targeted source PO values."""
import json
from pathlib import Path
from django.utils.translation import gettext,override
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
baseline=json.loads((ROOT/'docs/qa/place-qa06-plan-2026-10-10/catalog-comparison.json').read_text(encoding='utf-8'))
rows=[]
for row in baseline['rows']:
    expected=row['source_translation'] or row['msgid']
    with override(row['language']):actual=gettext(row['msgid'])
    assert actual==expected,(row['language'],row['msgid'],actual,expected)
    rows.append({'language':row['language'],'msgid':row['msgid'],'actual':actual,'expected':expected,'pass':True})
for lang,values in [('ru',['Бизнес','Общественное место']),('az',['Biznes','İctimai məkan']),('en',['Business','Public space'])]:
    for key,expected in zip(['Бизнес','Общественное место'],values):
        with override(lang):actual=gettext(key)
        assert actual==expected
        rows.append({'language':lang,'msgid':key,'actual':actual,'expected':expected,'pass':True})
result={'checks':len(rows),'rows':rows,'LOCALE_PATHS':[str(p) for p in settings.LOCALE_PATHS]}
(HERE/'locale-runtime.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(f'{len(rows)} runtime gettext checks passed from verified isolated catalogues.')
