"""Additional clean synthetic venue; audited offering transitions remain UI only."""
import sys,json
sys.argv=['run.py','qa-bootstrap']
from run import *
from catalog.models import Place,Subcategory
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
p=Place.objects.create(name='Uydurma fresh',name_az='Uydurma fresh',name_ru='Вымышленное новое место',name_en='Fictional fresh place',description_az='Uşaqlar üçün uydurma yerli fəaliyyət mərkəzi. '*10,category_id='SPRT',subcategory=Subcategory.objects.filter(category_id='SPRT',is_active=True).first(),owner=get_user_model().objects.get(pk=1),created_by_id=1,status='published',is_active=True,city='baku',district='baku_yasamal',address='Uydurma küçə 16 fresh',phone1='+994500000016',schedule_mode='always_open',price_mode='tariffs',age_from=3,age_to=17)
p.photo.save('synthetic-fresh.png',ContentFile((STATE/'assets/photo.png').read_bytes()),save=True)
f=json.loads((HERE/'fixtures.json').read_text());f['venues']['localfresh']=p.pk;(HERE/'fixtures.json').write_text(json.dumps(f,indent=2),encoding='utf-8');print('Additional fresh venue id',p.pk)
