"""Correct own initial venue fixture typo; not an audited application transition."""
import sys
sys.argv=['run.py','qa-bootstrap']
from run import *
from catalog.models import Place,Activity,Subcategory
assert not Activity.objects.exists()
sub=Subcategory.objects.filter(category_id='SPRT',is_active=True).first();assert sub
assert Place.objects.filter(price_mode='paid').count()==3
Place.objects.filter(price_mode='paid').update(price_mode='tariffs',subcategory=sub)
Place.objects.filter(pk=3).update(schedule_mode='regular')
print('Initial fixture invalid enum paid corrected to actual tariffs; valid subcategory; legacy mode regular. No offerings touched.')
