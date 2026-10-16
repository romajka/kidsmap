"""Targeted form validators under the same isolated setup, without DB writes."""
import json,runpy,sys
from pathlib import Path
H=Path(__file__).resolve().parent
sys.argv=[str(H/'runtime.py'),'whitespace-form-proof','field-runtime.json'];runpy.run_path(str(H/'runtime.py'),run_name='__main__')
from catalog.forms import AccountDeletionConfirmForm
from catalog.services.account_deletion import typed_confirmation_phrase
rows=[]
for lang in('ru','az','en'):
 for name,value,expected in [('empty','','required'),('overlong','x'*81,'max_length'),('exact',typed_confirmation_phrase(lang),None),('padded',' '+typed_confirmation_phrase(lang)+' ',None)]:
  form=AccountDeletionConfirmForm(data={'form_action':'confirm','confirmation_code':'000001','typed_confirmation':value});valid=form.is_valid();errors=form.errors.as_data().get('typed_confirmation',[])
  ok=(valid and form.cleaned_data['typed_confirmation']==value)if expected is None else(not valid and any(e.code==expected for e in errors))
  rows.append({'lang':lang,'case':name,'pass':ok})
(H/'form-guards.json').write_text(json.dumps({'rows':rows,'DB_writes':False},indent=2));print(json.dumps({'guards':len(rows),'pass':sum(x['pass']for x in rows)}));sys.exit(0 if all(r['pass']for r in rows)else 1)
