from pathlib import Path
here=Path(__file__).resolve().parent
p=here/'observe.py'
s=p.read_text(encoding='utf-8').replace("OrganizationTeamInvitation.objects.values('id','organization_id','status','role','version')", "OrganizationTeamInvitation.objects.values('id','organization_id','status','role','base_ownership_version')")
p.write_text(s,encoding='utf-8')
