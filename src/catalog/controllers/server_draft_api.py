"""CSRF-protected JSON transport for private server drafts."""
import json
import logging

logger=logging.getLogger(__name__)
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from catalog.models import ServerDraft
from catalog.services import server_drafts as service


def _error(name, status, data=None, draft=None):
    result={'status':name,'errors':{'__all__':[name]}}
    if isinstance(data,dict) and isinstance(data.get('fields'),dict): result['submitted_fields']=data['fields']
    if draft: result.update({k:v for k,v in service.serialize(draft, include_fields=False).items() if k not in {'status','errors'}})
    return JsonResponse(result,status=status)


@never_cache
@csrf_protect
@require_http_methods(['GET','POST'])
def draft_collection(request):
    if not request.user.is_authenticated or not request.user.is_active: return _error('forbidden',403)
    if request.method=='GET':
        rows=[]
        for draft in ServerDraft.objects.filter(actor=request.user).order_by('-saved_at')[:100]:
            try: service.read(user=request.user,draft_id=draft.pk)
            except (PermissionDenied,ValidationError,ServerDraft.DoesNotExist): continue
            rows.append(service.serialize(draft,include_fields=False))
        return JsonResponse({'drafts':rows})
    data=None
    try:
        if request.content_type!='application/json' or len(request.body)>65536: raise ValidationError('JSON required.')
        data=json.loads(request.body)
        if not isinstance(data,dict) or set(data)-{'draft_id','target_type','target_id','schema_version','source_version','expected_version','fields'}: raise ValidationError('Invalid JSON fields.')
        draft=service.save(user=request.user,data=data)
        return JsonResponse(service.serialize(draft),status=200 if data.get('draft_id') else 201)
    except service.DraftConflict as exc: return _error('conflict',409,data,exc.draft)
    except PermissionDenied: return _error('forbidden',403,data)
    except ServerDraft.DoesNotExist: return _error('not_found',404,data)
    except (ValidationError,ValueError,KeyError,TypeError,json.JSONDecodeError): return _error('invalid_request',400,data)
    except Exception:
        logger.exception("Draft save unavailable")
        return _error('unavailable',503,data)


@never_cache
@csrf_protect
@require_http_methods(['GET'])
def draft_detail(request,draft_id):
    if not request.user.is_authenticated or not request.user.is_active: return _error('forbidden',403)
    try: return JsonResponse(service.serialize(service.read(user=request.user,draft_id=draft_id)))
    except PermissionDenied: return _error('forbidden',403)
    except ServerDraft.DoesNotExist: return _error('not_found',404)
    except ValidationError: return _error('invalid_request',400)


@never_cache
@csrf_protect
@require_http_methods(['GET','POST'])
def draft_photo(request,draft_id):
    if not request.user.is_authenticated or not request.user.is_active: return _error('forbidden',403)
    if request.method=='GET':
        from django.http import FileResponse
        try:
            draft=service.read(user=request.user,draft_id=draft_id)
            if not draft.photo_name: return _error('not_found',404)
            return FileResponse(service.private_storage().open(draft.photo_name,'rb'),content_type='image/webp',as_attachment=True,filename='draft.webp')
        except PermissionDenied: return _error('forbidden',403)
        except (ServerDraft.DoesNotExist,FileNotFoundError): return _error('not_found',404)
        except ValidationError: return _error('invalid_request',400)
    data={'fields':{}}
    try:
        if set(request.POST)-{'expected_version'} or set(request.FILES)-{'photo'}: raise ValidationError('Invalid upload fields.')
        expected=int(request.POST['expected_version'])
        draft=service.upload_photo(user=request.user,draft_id=draft_id,expected_version=expected,file=request.FILES.get('photo'))
        return JsonResponse(service.serialize(draft))
    except service.DraftConflict as exc: return _error('conflict',409,data,exc.draft)
    except PermissionDenied: return _error('forbidden',403)
    except ServerDraft.DoesNotExist: return _error('not_found',404)
    except (ValidationError,ValueError,KeyError,TypeError): return _error('invalid_upload',422)


@never_cache
@csrf_protect
@require_http_methods(['POST'])
def draft_materialize(request,draft_id):
    if not request.user.is_authenticated or not request.user.is_active: return _error('forbidden',403)
    data=None
    try:
        if request.content_type!='application/json' or len(request.body)>1024: raise ValidationError('JSON required.')
        data=json.loads(request.body)
        if not isinstance(data,dict) or set(data)!={'expected_version'}: raise ValidationError('Invalid materialization payload.')
        draft,errors=service.materialize_place(user=request.user,draft_id=draft_id,expected_version=data['expected_version'],request=request)
        if errors:
            payload=service.serialize(draft);payload.update(status='validation_error',errors=errors)
            return JsonResponse(payload,status=422)
        return JsonResponse(service.serialize(draft))
    except service.DraftConflict as exc: return _error('conflict',409,data,exc.draft)
    except PermissionDenied: return _error('forbidden',403,data)
    except ServerDraft.DoesNotExist: return _error('not_found',404,data)
    except (ValidationError,ValueError,KeyError,TypeError,json.JSONDecodeError): return _error('invalid_request',400,data)
