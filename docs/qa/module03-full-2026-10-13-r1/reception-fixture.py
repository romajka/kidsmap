"""Complete the fictional receiving-place fixture; no tested UI transition seeded."""
import json
from pathlib import Path
from catalog.models import Place
from catalog.services.content_quality import public_place_queryset
P=Path(__file__).resolve().parent
f=json.loads((P/'fixtures.json').read_text());place=Place.objects.get(pk=f['place'])
place.age_from=3;place.age_to=12;place.description_az='Uydurma qəbul məkanı haqqında məlumat. '*12;place.description_ru='Вымышленное место приёма для локальной проверки. '*12;place.description_en='Fictional isolated reception description. '*12
place.save();assert public_place_queryset(Place.objects.filter(pk=place.pk)).exists()
print('Fictional reception now satisfies canonical public visibility; application unchanged.')
