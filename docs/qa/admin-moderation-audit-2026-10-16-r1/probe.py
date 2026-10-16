"""Run only through the owned runtime; native HTTP actions on fictional rows."""
from django.contrib.auth import get_user_model
from django.test import Client,override_settings
from django.contrib import admin
from catalog.models import PlaceReview
from catalog.services.content_quality import approved_review_queryset
from catalog.services.review_versions import moderate_candidate
from catalog.proxy_apps.catalog_moderation.models import ModerationReview
from catalog.services.review_versions import review_types
from django.urls import reverse
from django.utils.translation import override
f=json.loads((S/'fixtures.json').read_text());c=Client();staff=get_user_model().objects.get(username=f['username']);c.force_login(staff)
out={};rows=[]
def state(pk):
 h=PlaceReview.objects.get(pk=pk)
 return {'id':h.pk,'status':h.status,'approved':h.is_approved,'current':h.current_revision_id,'candidate':h.candidate_revision_id,'candidate_status':h.candidate_revision.status if h.candidate_revision_id else None,'text':h.text,'public':approved_review_queryset(PlaceReview.objects.filter(pk=h.pk)).exists()}
out['after_browser_bulk']=state(f['reviews'][0]['head'])
out['pending_candidates']=list(PlaceReview.objects.filter(is_current=True,candidate_revision__status='pending').values_list('pk',flat=True))
resp=c.get('/admin/catalog_moderation/moderationreview/')
out['queue_after_bulk']={'status':resp.status_code,'ids':list(resp.context_data['cl'].queryset.values_list('pk',flat=True))}
with override('ru'):
 r=c.get('/admin/catalog/placereview/?review_status=suspicious');out['needs_check_filter']={'status':r.status_code,'ids':list(r.context_data['cl'].queryset.values_list('pk',flat=True))}
 # Single legacy approval on a first candidate.
 h=f['reviews'][2]['head'];r=c.post(f'/admin/catalog/placereview/{h}/approve/');out['single_approve']={'response':r.status_code,'state':state(h)}
 # Single legacy hiding of an existing published review with pending edit.
 h=f['reviews'][1]['head'];before=state(h);r=c.post(f'/admin/catalog/placereview/{h}/hide/');out['single_hide']={'response':r.status_code,'before':before,'after':state(h)}
 # Correct typed approval control, with explicit revision id.
 h=f['reviews'][3]['head'];before=state(h);r=c.post(reverse('typed_review_action',args=['place',h,'approve']),{'revision_id':before['candidate']});out['typed_approval_control']={'response':r.status_code,'before':before,'after':state(h)}
 # Pending place: read-only preview cannot use its public URL.
 p=c.get('/admin/catalog_moderation/moderationplace/'+str(f['pending_place'])+'/change/')
 from catalog.models import Place
 place=Place.objects.get(pk=f['pending_place']);url=place.get_absolute_url();r=c.get(url);out['pending_place_public_preview']={'editor_status':p.status_code,'public_status':r.status_code,'url':url}
 # Repeat moderation of an already-decided version fails safely.
 h=f['reviews'][3]['head'];r=c.post(reverse('typed_review_action',args=['place',h,'approve']),{'revision_id':before['candidate']});out['repeat_decision_control']=r.status_code
 # Host routing control: explicit isolated sessions and canonical public host.
 with override_settings(ADMIN_HOST='admin.audit.invalid',PUBLIC_BASE_URL='https://public.audit.invalid'):
  public=Client();r=c.get(reverse('typed_reviews',args=['place',f['place']]),HTTP_HOST='admin.audit.invalid',secure=True)
  guest=public.get(reverse('typed_reviews',args=['place',f['place']]),HTTP_HOST='public.audit.invalid',secure=True)
  out['host_routing']={'admin_response':r.status_code,'location':r.get('Location'),'public_response':guest.status_code,'public_candidate_blocks':guest.content.count(b'data-candidate-id')}
out['mro']={'approve_owner':admin.site._registry[PlaceReview].approve_view.__func__.__qualname__,'toggle_owner':admin.site._registry[PlaceReview]._toggle_review_visibility.__func__.__qualname__,'proxy_bulk_owner':admin.site._registry[ModerationReview].approve_selected.__func__.__qualname__}
out['testing']=settings.TESTING;out['synthetic_only']=True
report=S.parents[1]/'docs/qa'/S.name
(report/'probe.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
print(json.dumps(out,ensure_ascii=False))
