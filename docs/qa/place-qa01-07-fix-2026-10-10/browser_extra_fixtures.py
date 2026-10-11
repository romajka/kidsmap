"""Own database preparation for browser readbacks; no application shortcuts."""
import json
from decimal import Decimal
from pathlib import Path
from django.urls import reverse
from catalog.models import Place,Category,Subcategory
from catalog.testcases.utils import ensure_quality_subcategory
HERE=Path(__file__).resolve().parent
place=Place.objects.get(pk=2);plan=place.pricing_plan_records.get();plan.price=Decimal('15.00');plan.save()
cat,_=Category.objects.get_or_create(code='KMFIX_NEXT',defaults={'name':'KMFIX Next category','name_ru':'KMFIX Следующая категория','name_az':'KMFIX Növbəti kateqoriya','name_en':'KMFIX Next category'})
sub=ensure_quality_subcategory(cat)
Subcategory.objects.filter(pk=sub.pk).update(name_ru='KMFIX Новая подкатегория',name_az='KMFIX Yeni alt kateqoriya',name_en='KMFIX New subcategory')
metadata={'published_fixture_id':place.pk,'next_category':cat.code,'next_subcategory':sub.pk,
          'create_url':reverse('owner_place_create'),'review_fixture_url':reverse('admin:volunteer_review',args=[2]),
          'public_fixture_url':place.get_absolute_url()}
(HERE/'browser-fixtures.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8')
print(json.dumps(metadata))
