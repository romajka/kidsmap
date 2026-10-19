import sys,json,subprocess
sys.path.insert(0,'/mnt/c/kidsmap/.tmp/m10-seq-r1')
from stage_apply import *
S=O/'stages/SITE10';red=json.loads((S/'evidence/red-backend.json').read_text());assert len(red['failures'])==24 and not red['errors']
(S/'IMPLEMENTATION_PLAN.md').write_text('# SITE10 plan — ongoing immediate-fix authorization\n\nReplace all4retired blank410 responses (events list/detail and temporary Place canonical/legacy) with shared localized HTML410, exact noindex/follow metadata and working home/catalog links. Preserve OFF/ON visibility and HTTP410; no redirects or data changes. Accessible singlemain/h1, keyboard links44pxmin, responsive wrapping in scoped newCSS. Scope views.py,newpublic_unavailable template/CSS,new4method regression,2newgettext messages in3PO catalogues. Build current isolated3localeMO in own scratch, sharedMO untouched. FreshRED4methods24expected missingheading/noindex observations with destination/read-only controlsPASS. Verify cumulative backend +native3languages6widths/events+temporary routes, native toggle restoration, actual browser navigation (previous blank410 failed) and keyboard recovery. Known SITE18header1280 remains separatelyOPEN.\n')
path='src/catalog/views.py';t=(R/path).read_bytes().decode();nl='\r\n' if '\r\n' in t else '\n';old='return HttpResponseGone()';assert t.count(old)==4;t=t.replace(old,'return _retired_public_page(request)')
anchor='def events_landing(request):';assert t.count(anchor)==1;t=t.replace(anchor,('def _retired_public_page(request):\n    return render(request, "pages/public_unavailable.html", status=410)\n\n\n').replace('\n',nl)+anchor)
template='''{% extends "base.html" %}
{% load i18n static %}
{% block title %}{% trans "Страница недоступна" %} · {{ brand_name }}{% endblock %}
{% block title_plain %}{% trans "Страница недоступна" %}{% endblock %}
{% block title_plain_twitter %}{% trans "Страница недоступна" %}{% endblock %}
{% block robots_meta %}noindex, follow{% endblock %}
{% block googlebot_meta %}noindex, follow{% endblock %}
{% block meta_description %}{% trans "Посмотрите доступные места и занятия в каталоге." %}{% endblock %}
{% block extra_head %}<link rel="stylesheet" href="{% static 'css/pages/public_unavailable.css' %}" />{% endblock %}
{% block content %}
<section class="public-unavailable" aria-labelledby="unavailable-heading">
  <h1 id="unavailable-heading">{% trans "Страница недоступна" %}</h1>
  <p>{% trans "Посмотрите доступные места и занятия в каталоге." %}</p>
  <div class="public-unavailable-actions">
    <a class="btn" href="{% url 'place_list' %}">{% trans "Каталог" %}</a>
    <a href="{% url 'home' %}">{% trans "На главную" %}</a>
  </div>
</section>
{% endblock %}
'''
css='''.public-unavailable {
  max-width: 720px; margin: clamp(40px, 8vw, 96px) auto;
  padding: 0 20px; overflow-wrap: anywhere;
}
.public-unavailable h1 { margin: 0 0 16px; font-size: clamp(28px, 5vw, 44px); line-height: 1.15; }
.public-unavailable p { margin: 0 0 28px; max-width: 55ch; line-height: 1.6; }
.public-unavailable-actions { display: flex; flex-wrap: wrap; align-items: center; gap: 16px 24px; }
.public-unavailable-actions a { display: inline-flex; align-items: center; min-height: 44px; max-width: 100%; }
.public-unavailable-actions a:focus-visible { outline: 3px solid currentColor; outline-offset: 4px; }
'''
files={path:t.encode(),'src/catalog/templates/pages/public_unavailable.html':template.encode(),'static/css/pages/public_unavailable.css':css.encode(),'src/catalog/testcases/test_site_qa10_retired_recovery.py':(Q/'test_site10_candidate.py').read_bytes()}
translations={'az':['Bu səhifə əlçatan deyil','Mövcud məkan və məşğələlərə kataloqda baxın.'],'ru':['Страница недоступна','Посмотрите доступные места и занятия в каталоге.'],'en':['This page is unavailable','Explore available places and activities in the catalogue.']};msgs=['Страница недоступна','Посмотрите доступные места и занятия в каталоге.']
for lang,values in translations.items():
 rel='locale/'+lang+'/LC_MESSAGES/django.po';before=(R/rel).read_bytes();text=before.decode();pnl='\r\n' if '\r\n' in text else '\n';extra=''
 for msg,value in zip(msgs,values):
  assert ('msgid '+json.dumps(msg,ensure_ascii=False)) not in text
  extra+='\n#: src/catalog/templates/pages/public_unavailable.html\nmsgid '+json.dumps(msg,ensure_ascii=False)+'\nmsgstr '+json.dumps(value,ensure_ascii=False)+'\n'
 files[rel]=before+extra.replace('\n',pnl).encode()
apply('10',files)
cmd=['docker','exec','m10seq-r1-app','python',str(R/'scripts/build_isolated_locales.py'),'build','--source-locale',str(R/'locale'),'--output',str(Q/'locales-site10'),'--compiler','native'];p=subprocess.run(cmd,capture_output=True,text=True);(S/'evidence/locale-build.txt').write_text(p.stdout+p.stderr);assert p.returncode==0,p.stderr
stage=json.loads((Q/'stage.json').read_text());(S/'evidence/stage-before-locale.json').write_text(json.dumps(stage,indent=2));stage['locales']='locales-site10';(Q/'stage.json').write_text(json.dumps(stage));(S/'evidence/locale-build.json').write_text(json.dumps({'command':cmd,'exit':p.returncode,'isolated_locales':'az,ru,en','shared_MO_untouched':True},indent=2));print('SITE10 localized HTML410 applied, isolated3localeMO compiled.')
