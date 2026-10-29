"""GET-only staff adapters over the shared identity registry."""
import json
from urllib.parse import urlencode
from django.core.exceptions import PermissionDenied, BadRequest, ValidationError
from django.core.paginator import Paginator, InvalidPage
from django.http import Http404, HttpResponse, JsonResponse
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.translation import get_language
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET
from catalog.models import Place, VolunteerPlaceRevision
from catalog.services.place_identity import identity_registry, check_duplicates, FIELDS
from catalog.services.place_identity_copy import identity_copy


def _snapshot(model_admin, request, places=None, exclude_draft_id=None):
    if not model_admin.has_view_or_change_permission(request): raise PermissionDenied
    return identity_registry(request.user, places=places,exclude_draft_id=exclude_draft_id,
        can_view=lambda obj:model_admin.has_view_or_change_permission(request,obj),
        can_edit=lambda obj:model_admin.has_change_permission(request,obj))


def _json(data, filename):
    response=HttpResponse(json.dumps(data,ensure_ascii=False,indent=2),content_type='application/json')
    response['Content-Disposition']=f'attachment; filename="{filename}.json"'
    response['Cache-Control']='private, no-store'
    return response


def _urls(model_admin, record):
    if record['id'] is not None:
        return {'url':reverse('admin:catalog_place_change',args=[record['id']]),
                'compare_url':reverse('admin:catalog_place_identity_compare',args=[record['id']])}
    return {'url':reverse('admin:catalog_place_add')+'?'+urlencode({'type':'permanent',
        'draft_id':record['draft_id'],'draft_session':record['draft_id']}), 'compare_url':''}


def _title(fields):
    language=(get_language() or 'az').split('-')[0]
    return fields.get('name_'+language) or next((fields[k] for k in ('name_az','name_ru','name_en','name') if fields.get(k)),'—')


def _present(model_admin, record, ui):
    fields=record.get('match_fields') or record['versions'][-1]['fields']
    return {**record, **_urls(model_admin,record), 'title':_title(fields), 'address':fields['address'],
        'classification_label':ui.get(record.get('classification',''),''),
        'versions':[{**v,'source_label':ui[v['source']]} for v in record['versions']],
        'evidence':[{**e,'source_label':ui[e['source']],
                     'signal_labels':', '.join(str(Place._meta.get_field(f).verbose_name) for f in e.get('matched_fields',[])) or ', '.join(ui.get(s,s) for s in e['signals'])} for e in record.get('evidence',[])]}


def _query(request):
    values={name:str(request.GET.get(name,'')).strip()[:1000] for name in
            ('name','name_az','name_ru','name_en','address','phone','phone1','phone2','phone3','website','instagram','lat','lng')}
    raw=request.GET.get('public_links','')
    if raw:
        from catalog.services.place_public_links import normalize_public_links
        try:
            if len(raw)>8192:raise ValueError
            values['public_links']=normalize_public_links(json.loads(raw))
        except (ValueError,TypeError,ValidationError):raise BadRequest('Invalid public links')
    return values


def _page(request, rows):
    try:
        size=int(request.GET.get('page_size',25)); number=int(request.GET.get('page',1))
        if not 1<=size<=100 or number<1: raise ValueError
        return Paginator(rows,size).page(number)
    except (ValueError,InvalidPage): return None


def _page_url(request,number,snapshot_id):
    params=request.GET.copy();params['page']=number;params['snapshot']=snapshot_id
    return '?'+params.urlencode()


@never_cache
@require_GET
def registry_view(request,model_admin):
    snapshot=_snapshot(model_admin,request);ui=identity_copy()
    if request.GET.get('format')=='json': return _json(snapshot,'kidsmap-duplicate-registry')
    query=_query(request)
    result=check_duplicates(request.user,query,exclude_place_id=request.GET.get('exclude'),registry=snapshot) if any(query.values()) else None
    if request.GET.get('snapshot') and request.GET['snapshot']!=snapshot['snapshot_id']:
        return HttpResponse(ui['snapshot_changed'],status=409)
    page=_page(request,result['results'] if result else snapshot['records'])
    if page is None:return HttpResponse('Invalid page',status=400)
    context={**model_admin.admin_site.each_context(request),'title':ui['title'],'ui':ui,
        'opts':model_admin.opts,'snapshot':snapshot,'rows':[_present(model_admin,r,ui) for r in page.object_list],
        'query':query,'checked':result is not None,'page':page,
        'back_url':reverse('admin:catalog_place_changelist'),
        'export_url':reverse('admin:catalog_place_identity_registry')+'?format=json',
        'next_url':_page_url(request,page.next_page_number(),snapshot['snapshot_id']) if page.has_next() else '',
        'previous_url':_page_url(request,page.previous_page_number(),snapshot['snapshot_id']) if page.has_previous() else ''}
    return TemplateResponse(request,'admin/catalog/place/identity_registry.html',context)


@never_cache
@require_GET
def comparison_view(request,model_admin,object_id):
    snapshot=_snapshot(model_admin,request,Place.objects.filter(pk=object_id))
    record=next((r for r in snapshot['records'] if r['id']==object_id),None)
    if record is None:raise Http404
    if request.GET.get('format')=='json':
        return _json({**snapshot,'export_scope':'identity_comparison','records':[record]},f'place-{object_id}-identities')
    ui=identity_copy();versions=[{**v,'source_label':ui[v['source']],
        'status_label':ui['own_draft'] if v['source']=='own_draft' else dict(VolunteerPlaceRevision.Status.choices if v['source']=='candidate' else Place.STATUS_CHOICES).get(v['status'],v['status'])} for v in record['versions']]
    table=[]
    for field in FIELDS:
        values=[v['fields'][field] for v in versions]
        table.append({'label':Place._meta.get_field(field).verbose_name,
            'cells':[{'value':'\n'.join(row['label']+': '+row['url'] for row in value) if isinstance(value,list) else value if value not in (None,'') else '—','changed':i>0 and value!=values[0]}
                     for i,value in enumerate(values)]})
    context={**model_admin.admin_site.each_context(request),'title':ui['compare_title'],'ui':ui,
        'opts':model_admin.opts,'record':record,'versions':versions,'table':table,'snapshot':snapshot,
        'edit_url':reverse('admin:catalog_place_change',args=[object_id]),
        'back_url':reverse('admin:catalog_place_identity_registry'),
        'export_url':reverse('admin:catalog_place_identity_compare',args=[object_id])+'?format=json'}
    return TemplateResponse(request,'admin/catalog/place/identity_compare.html',context)


@never_cache
@require_GET
def matching_view(request,model_admin):
    snapshot=_snapshot(model_admin,request,exclude_draft_id=request.GET.get('exclude_draft_id'));ui=identity_copy()
    if request.GET.get('snapshot') and request.GET['snapshot']!=snapshot['snapshot_id']:
        return JsonResponse({'ok':False,'message':ui['snapshot_changed']},status=409)
    result=check_duplicates(request.user,_query(request),exclude_place_id=request.GET.get('exclude'),registry=snapshot)
    page=_page(request,result['results'])
    if page is None:return JsonResponse({'ok':False,'message':'Invalid page'},status=400)
    rows=[]
    for record in page.object_list:
        row=_present(model_admin,record,ui)
        row['matched']=[ui.get(s,s) for s in record['matched']]
        rows.append(row)
    query=request.GET.copy();query.pop('page',None);query.pop('snapshot',None)
    return JsonResponse({**result,'results':rows,'page':page.number,'page_size':page.paginator.per_page,
        'has_next':page.has_next(),'snapshot_id':snapshot['snapshot_id'],
        'next_url':_page_url(request,page.next_page_number(),snapshot['snapshot_id']) if page.has_next() else None,
        'registry_url':reverse('admin:catalog_place_identity_registry')+'?'+query.urlencode()})
