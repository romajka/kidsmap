"""Stage06 server contracts; no cabinet forms or frontend rules."""
import json
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied, ValidationError
from django.http import JsonResponse
from django.urls import reverse
from catalog.services.organization_connections import detach_access
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from catalog.services import organization_ownership as service


def _integer(value):
    if not isinstance(value,int) or isinstance(value,bool) or value<1:raise ValidationError('Positive integer required.')
    return value


@require_POST
@csrf_protect
def organization_ownership_action(request,action,target_type,target_id):
    if not request.user.is_authenticated or not request.user.is_active:return JsonResponse({'error':'forbidden'},status=403)
    specs={'create':{'values','allow_separate'},'claim':{'note'},'approve-claim':{'approve','note'},'join':{'organization_id','relationship_kind'},'confirm-join':set(),'cancel-join':{'expected_state'},'approve-info':set(),'detach':{'organization_id','expected_ownership_version'},'transfer':{'new_owner_id','expected_ownership_version'}}
    if action not in specs or target_type not in ('place','organization'):return JsonResponse({'error':'unknown_action'},status=404)
    if action in ('join','confirm-join','cancel-join','approve-info','detach') and target_type!='place':return JsonResponse({'error':'invalid_target'},status=400)
    try:
        if request.content_type!='application/json' or len(request.body)>65536:raise ValidationError('JSON payload required.')
        data=json.loads(request.body)
        if not isinstance(data,dict) or set(data)-specs[action]:raise ValidationError('Unsupported fields.')
        for key in ('organization_id','expected_ownership_version','new_owner_id'):
            if key in data:data[key]=_integer(data[key])
        if 'note' in data and (not isinstance(data['note'],str) or len(data['note'])>5000):raise ValidationError('Invalid note.')
        if 'relationship_kind' in data and data['relationship_kind'] not in ('business','informational'):raise ValidationError('Invalid relationship.')
        if 'approve' in data and not isinstance(data['approve'],bool):raise ValidationError('Invalid approval.')
        if action=='create':
            if target_id!=0:raise ValidationError('Creation has no existing target ID.')
            method=service.create_place if target_type=='place' else service.create_organization
            row=method(actor=request.user,**data)
        else:
            _integer(target_id)
            if action=='claim':row=service.submit_claim(actor=request.user,target_type=target_type,target_id=target_id,**data)
            elif action=='approve-claim':row=service.moderate_claim(actor=request.user,target_type=target_type,request_id=target_id,**{'approve':True,**data})
            elif action=='join':row=service.request_join(actor=request.user,place_id=target_id,**data)
            elif action=='confirm-join':row=service.confirm_join(actor=request.user,request_id=target_id)
            elif action=='cancel-join':
                if set(data) != {'expected_state'}: raise ValidationError('State required.')
                row=service.cancel_join(actor=request.user,request_id=target_id,**data)
                return JsonResponse({'request_id':row.pk,'status':row.status})
            elif action=='approve-info':row=service.approve_informational_join(actor=request.user,request_id=target_id)
            elif action=='detach':
                if set(data) != specs['detach']: raise ValidationError('Organization and ownership version required.')
                detach_access(actor=request.user,place_id=target_id,**data)
                return JsonResponse({'error':'confirmation_required','preview_url':reverse(
                    'organization_detach_preview',args=[data['organization_id'],target_id])},status=409)
            else:row=service.transfer_owner(actor=request.user,target_type=target_type,target_id=target_id,**data)
        response={'id':row.pk,'status':getattr(row,'status',None)}
        if action in ('join','confirm-join','approve-info','claim'):response['request_id']=row.pk
        if hasattr(row,'ownership_version'):response['ownership_version']=row.ownership_version
        return JsonResponse(response)
    except PermissionDenied:return JsonResponse({'error':'forbidden'},status=403)
    except ObjectDoesNotExist:return JsonResponse({'error':'not_found'},status=404)
    except (json.JSONDecodeError,UnicodeDecodeError,TypeError,ValidationError) as exc:
        if getattr(exc,'code',None)=='request_conflict':
            return JsonResponse({'error':'request_conflict','reload_required':True},status=409)
        if getattr(exc,'code',None)=='structure_changed':
            return JsonResponse({'error':'structure_changed','reload_required':True},status=409)
        duplicate=getattr(exc,'code',None)=='possible_duplicate'
        return JsonResponse({'error':'possible_duplicate' if duplicate else 'invalid_request','create_separate_available':duplicate},status=409 if duplicate else 400)
