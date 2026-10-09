import json
from catalog.models import Place, VolunteerPlaceRevision
from catalog.services.pricing_plans import serialize_nested_pricing
from catalog.services.place_schedule import serialize_place_schedule
rows=[]
for place in Place.objects.order_by('pk'):
    revision=VolunteerPlaceRevision.objects.filter(place=place).first()
    rows.append(dict(id=place.pk,name_az=place.name_az,status=place.status,is_public=place.is_public,
        nature=place.nature,nested=serialize_nested_pricing(place),schedule_mode=place.schedule_mode,schedule=serialize_place_schedule(place),name_ru=place.name_ru,name_en=place.name_en,
        url=place.get_absolute_url(),organization_id=place.organization_id,
        content_version=place.content_version,photo=place.photo.name,
        gallery=list(place.gallery.order_by('order','pk').values('id','image','order')),
        pricing=place.pricing_plans,activities=list(place.activities.values('id','name_az')) if hasattr(place,'activities') else [],
        revision=dict(id=revision.pk,status=revision.status,version=revision.version,
            changed_fields=revision.changed_fields,payload=revision.payload) if revision else None))
print(json.dumps(rows,ensure_ascii=False,default=str))
