import difflib,hashlib,json,subprocess
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=R/'docs/qa/module10-sequential-2026-10-18-pc-r1';Q=R/'.tmp/m10-seq-r1';S=O/'stages/SITE05';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
n=json.loads((O/'evidence/browser-site05-baseline.json').read_text());assert len([r for r in n['rows'] if r.get('checks',{}).get('uploaded_banner_rendered') is False])==6 and not n['pageerrors'] and not n['local_errors']
assert json.loads((S/'evidence/red-backend.json').read_text())['exit']==1
for name in ['candidate','entry-source']:(S/name).mkdir(exist_ok=True)
path='src/catalog/templates/pages/home.html';raw=(R/path).read_bytes();t=raw.decode();nl='\r\n' if '\r\n' in t else '\n';old='<section class="home-hero panel animate-on-scroll is-visible">';assert t.count(old)==1
new='''<section class="home-hero panel animate-on-scroll is-visible{% if site_settings.home_hero_image or site_settings.home_hero_mobile_image %} home-hero-has-background{% endif %}">
  {% if site_settings.home_hero_image or site_settings.home_hero_mobile_image %}
  <picture class="home-hero-background" aria-hidden="true">
    {% if site_settings.home_hero_mobile_image %}
    <source media="(max-width: 760px)" srcset="{{ site_settings.home_hero_mobile_image.url }}" />
    {% endif %}
    <img src="{% if site_settings.home_hero_image %}{{ site_settings.home_hero_image.url }}{% else %}{{ site_settings.home_hero_mobile_image.url }}{% endif %}"
      alt="" decoding="async" loading="eager" fetchpriority="high" />
  </picture>
  {% endif %}'''.replace('\n',nl);t=t.replace(old,new)
css='static/css/pages/home_redesign.css';cssraw=(R/css).read_bytes();ct=cssraw.decode();cnl='\r\n' if '\r\n' in ct else '\n';extra='''
/* Uploaded main-banner backgrounds retain the existing gallery and readable copy. */
body.page-home .home-hero.home-hero-has-background { isolation: isolate; }
body.page-home .home-hero-background {
  position: absolute; inset: 0; z-index: -1;
  display: block; overflow: hidden; border-radius: 24px;
  background: var(--home-paper); pointer-events: none;
}
body.page-home .home-hero-background img {
  display: block; width: 100%; height: 100%; object-fit: cover; opacity: .2;
}
'''.replace('\n',cnl);ct+=extra
files={path:(raw,t.encode()),css:(cssraw,ct.encode()),'src/catalog/testcases/test_site_qa05_home_background.py':(None,(Q/'test_site05_candidate.py').read_bytes())};sources=json.loads((Q/'expected-source.json').read_text())['sources'];metadata={};diff=''
for rel,(before,after) in files.items():
 assert before is not None or not (R/rel).exists()
 for name,data in [('candidate',after),('entry-source',before)]:
  if data is not None:p=S/name/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
 diff+=''.join(difflib.unified_diff((before or b'').decode().splitlines(True),after.decode().splitlines(True),fromfile='a/'+rel if before else '/dev/null',tofile='b/'+rel));metadata[rel]={'before':hashlib.sha256(before).hexdigest() if before else None,'after':hashlib.sha256(after).hexdigest()}
(S/'implemented.diff').write_text(diff,newline='');p=subprocess.run(['git','-C',str(R),'apply','--check',str(S/'implemented.diff')],capture_output=True,text=True);assert p.returncode==0,p.stderr
for rel,(_,after) in files.items():(R/rel).write_bytes(after);sources[rel]=sha(R/rel)
(Q/'expected-source.json').write_text(json.dumps({'sources':sources},indent=2));(S/'source-applied.json').write_text(json.dumps({'sources':sources},indent=2));(S/'applied.json').write_text(json.dumps({'files':metadata,'source_count':len(sources),'apply_check_exit':0},indent=2));print('SITE05 decorative responsive banner background applied; gallery retained.')
