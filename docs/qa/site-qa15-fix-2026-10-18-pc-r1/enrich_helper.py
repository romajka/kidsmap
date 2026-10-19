from pathlib import Path
Q=Path('/mnt/c/kidsmap/.tmp/site15-pc-fix-r1');p=Q/'qa_urls.py';s=p.read_text()
s=s.replace("role in ['content','super']","role in ['content','super','proxyfooter','viewer','denied','volunteer']")
needle="data['updated_at']=s.updated_at.isoformat()"
replace=needle+";data['logo']=s.logo.name or '';data['flags']={name:getattr(s,name) for name in ['events_section_enabled','specialists_section_enabled','organizations_section_enabled','public_favorites_count_enabled','public_favorites_minimum']};data['media_files']={p.relative_to(settings.MEDIA_ROOT).as_posix():__import__('hashlib').sha256(p.read_bytes()).hexdigest() for p in __import__('pathlib').Path(settings.MEDIA_ROOT).rglob('*') if p.is_file()};data['admin_log_count']=__import__('django.contrib.admin.models',fromlist=['LogEntry']).LogEntry.objects.count()"
assert needle in s;s=s.replace(needle,replace);p.write_text(s)
(Q/'extra_seed.py').write_bytes((Path(__file__).resolve().parent/'extra_seed.py').read_bytes())
print('Owned QA readback now includes media hashes/flags/log count; application untouched')
