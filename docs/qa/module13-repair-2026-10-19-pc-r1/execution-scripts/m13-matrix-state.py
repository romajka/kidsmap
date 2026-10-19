from pathlib import Path
R=Path('/mnt/c/kidsmap');Q=R/'.tmp/m13-full-r1';p=Q/'qa_urls.py';t=p.read_text();needle="urls[lang]={'organization':reverse('organization_detail',args=[org.public_id]),'place':p.get_absolute_url(),'online':Event.objects.get(pk=3).get_absolute_url()}";assert needle in t
t=t.replace(needle,"urls[lang]={'organization':reverse('organization_detail',args=[org.public_id]),'place':p.get_absolute_url(),'online':Event.objects.get(pk=3).get_absolute_url(),'specialist':__import__('catalog.models',fromlist=['Specialist']).Specialist.objects.get(pk=2).get_absolute_url(),'activity':reverse('activity_detail',args=[Activity.objects.get(program=program,archived_at__isnull=True).pk]),'physical':Event.objects.order_by('-pk').first().get_absolute_url()}")
p.write_text(t)
