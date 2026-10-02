"""CSRF-protected stage07 business-team contracts; no screen implementation."""
import json
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied, ValidationError
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST, require_GET
from catalog.services import business_team as service
from catalog.services.place_access import permission_configuration


@require_GET
def business_permission_config(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error':'forbidden'},status=403)
    return JsonResponse(permission_configuration())


@require_POST
@csrf_protect
def business_team_action(request,target_type,target_id,action):
    if not request.user.is_authenticated or not request.user.is_active:
        return JsonResponse({'error':'forbidden'},status=403)
    specs={'invite':{'email','role','actions','scope','place_ids'},'accept':{'invitation_id'},'reject':{'invitation_id'},'cancel':{'invitation_id'},'grant':{'grant_id','expected_version','active','role','actions','scope','place_ids'},'leave':{'grant_id'},'confirm':{'grant_id','expected_version'},'suspended':set(),'branch':{'values','allow_separate'}}
    if action not in specs or target_type not in ('place','organization'):
        return JsonResponse({'error':'unknown_action'},status=404)
    try:
        if request.content_type != 'application/json' or len(request.body) > 65536:
            raise ValidationError('JSON payload required.')
        data=json.loads(request.body)
        if not isinstance(data,dict) or set(data)-specs[action]:
            raise ValidationError('Unsupported fields.')
        # Nested IDs must belong to the route's target, even when the actor owns both.
        gm,im,field=service._models(target_type)
        for key,model in [('grant_id',gm),('invitation_id',im)]:
            if key in data:
                service._version(data[key])
                if not model.objects.filter(pk=data[key],**{field+'_id':target_id}).exists():
                    raise PermissionDenied
        if action in ('accept','reject','cancel','grant','leave','confirm'):
            data['expected_target_id']=target_id
        if action=='invite':row=service.invite(actor=request.user,target_type=target_type,target_id=target_id,**data)
        elif action=='accept':row=service.accept(actor=request.user,target_type=target_type,**data)
        elif action in ('reject','cancel'):row=service.decide_invitation(actor=request.user,target_type=target_type,cancel=action=='cancel',**data)
        elif action=='grant':row=service.change_grant(actor=request.user,target_type=target_type,**data)
        elif action=='leave':row=service.leave(actor=request.user,target_type=target_type,**data)
        elif action=='confirm':row=service.confirm_member(actor=request.user,target_type=target_type,**data)
        elif action=='branch':
            if target_type!='organization':raise ValidationError('Branch needs Organization.')
            row=service.create_branch(actor=request.user,organization_id=target_id,**data)
        else:
            rows=service.suspended(actor=request.user,target_type=target_type,target_id=target_id)
            return JsonResponse({'members':[{'id':r.pk,'member_id':r.member_id,'version':r.version,'role':r.role,'actions':r.actions,'scope':getattr(r,'scope','place')} for r in rows]})
        return JsonResponse({'id':row.pk,'version':getattr(row,'version',None),'status':getattr(row,'status',None)})
    except PermissionDenied:
        return JsonResponse({'error':'forbidden'},status=403)
    except ObjectDoesNotExist:
        return JsonResponse({'error':'not_found'},status=404)
    except service.TeamConflict:
        return JsonResponse({'error':'conflict'},status=409)
    except (json.JSONDecodeError,UnicodeDecodeError,TypeError,ValidationError):
        return JsonResponse({'error':'invalid_request'},status=400)
