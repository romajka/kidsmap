"""Only safe aggregates and synthetic records in our dedicated DB."""
import sys,json,hashlib
sys.argv=['run.py','observe']
from run import *
from catalog.models import Place,Organization,Activity,OfferingGroup,PricingPlan,OrganizationPlaceRequest,OrganizationGrant,OrganizationTeamInvitation
from catalog.services import organization_ownership,business_team
def preservation():
    rows=[]
    for p in Place.objects.filter(pk__in=range(1,11)).order_by('pk'):
        item={k:str(getattr(p,k)) for k in ['id','slug','owner_id','status','name_az','name_ru','name_en','description_az','address','city','district','schedule_mode','schedule','price_from','price_to']}
        item['photo']={'path':p.photo.name,'sha256':hashlib.sha256(Path(p.photo.path).read_bytes()).hexdigest()}
        item['gallery']=[{'id':g.pk,'order':g.order,'path':g.image.name,'sha256':hashlib.sha256(Path(g.image.path).read_bytes()).hexdigest()} for g in p.gallery.all()]
        item['days']=list(p.schedule_days.order_by('pk').values())
        item['activities']=list(Activity.objects.filter(place=p).order_by('pk').values())
        item['groups']=list(OfferingGroup.objects.filter(activity__place=p).order_by('pk').values())
        item['prices']=list(PricingPlan.objects.filter(place=p).order_by('pk').values())+list(PricingPlan.objects.filter(offering_group__activity__place=p).order_by('pk').values())
        rows.append(item)
    return rows
if len(sys.argv)>1:pass
filename=__import__('os').environ.get('QA_OBSERVATION','observation-current.json')
out={'preservation':preservation(),'organizations':list(Organization.objects.order_by('pk').values('id','name_az','name_ru','name_en','status','owner_id','content_version','ownership_version','public_id')),'links':[{'id':p.pk,'owner_id':p.owner_id,'ownership_version':p.ownership_version,'organization_id':p.organization_id,'current':bool(p.organization and organization_ownership.affiliation_current(p,p.organization)),'kind':p.organization_relationship_kind} for p in Place.objects.select_related('organization').order_by('pk')],'requests':list(OrganizationPlaceRequest.objects.values('id','place_id','organization_id','status','base_place_content_version','base_place_ownership_version','base_organization_ownership_version')),'grants':list(OrganizationGrant.objects.values('id','organization_id','member_id','is_active','role','version','scope','actions')),'invitations':list(OrganizationTeamInvitation.objects.values('id','organization_id','status','role','base_ownership_version'))}
(HERE/filename).write_text(json.dumps(out,indent=2,default=str,ensure_ascii=False),encoding='utf-8')
print('Safe synthetic observation saved:',filename)
