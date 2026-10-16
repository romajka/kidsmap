from catalog.models import Place
import json
fixture=json.loads((HERE/'fixtures.json').read_text());name='QA <img src=x onerror=alert(1)> "$&" '+('LongName'*10)
assert settings.DATABASES['default']['NAME']=='mod1213_fix_r1'
Place.objects.filter(pk=fixture['places']['edge']).update(name=name,name_az=name,name_ru=name,name_en=name)
fixture['edge_name']=name;(HERE/'fixtures.json').write_text(json.dumps(fixture,indent=2));print('Own long-name fixture initialized')
