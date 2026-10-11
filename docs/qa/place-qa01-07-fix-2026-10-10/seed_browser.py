"""Additional synthetic actors, stored session secrets only in ignored scratch."""
import json
import secrets
from django.contrib.auth import get_user_model
from django.test import Client
from catalog.models import Category
from catalog.testcases.utils import create_quality_place

U=get_user_model()
credentials={}
for role in ('owner','admin','other'):
    username='kmfix_synthetic_'+role
    password=secrets.token_urlsafe(24)
    actor,_=U.objects.get_or_create(username=username,defaults={'email':role+'@example.invalid'})
    actor.set_password(password)
    if role=='admin': actor.is_staff=actor.is_superuser=True
    actor.save()
    credentials[role]={'username':username,'password':password}
    c=Client();c.force_login(actor)
    state={'cookies':[{'name':settings.SESSION_COOKIE_NAME,'value':c.cookies[settings.SESSION_COOKIE_NAME].value,'domain':'127.0.0.1','path':'/','httpOnly':True,'secure':False,'sameSite':'Lax'}],'origins':[]}
    (settings.QA_ROOT/f'{role}-state.json').write_text(json.dumps(state),encoding='utf-8')
owner=U.objects.get(username=credentials['owner']['username'])
place=create_quality_place(owner=owner,created_by=owner,with_subcategory=True,with_pricing_plan=True,with_schedule_days=True)
Category.objects.create(code='KMFIX_LONG',name='KMFIX synthetic long category',
    name_ru='KMFIX Вымышленная категория для проверки длинного названия образовательных и творческих занятий',
    name_az='KMFIX Uzun kateqoriya adının yoxlanılması üçün uydurma təhsil və yaradıcılıq məşğələləri',
    name_en='KMFIX Synthetic category for testing a long educational and creative activities label')
credentials['place_id']=place.pk
(settings.QA_ROOT/'credentials.json').write_text(json.dumps(credentials),encoding='utf-8')
print('Synthetic actors and published fixture prepared; secrets retained only in ignored scratch.')
