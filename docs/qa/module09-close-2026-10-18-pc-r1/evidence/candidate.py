import json,hashlib,difflib,shutil
from pathlib import Path
R=Path('/mnt/c/kidsmap');Q=R/'.tmp/module09-pc-close-r1';O=R/'docs/qa/module09-close-2026-10-18-pc-r1';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
controller='src/catalog/controllers/typed_reviews.py';template='src/catalog/templates/catalog/review_reaction_conflict.html';test='src/catalog/testcases/test_social_qa12_reaction_conflict.py'
before=(R/controller).read_text();old='    except ReviewConflict:\n        return HttpResponse(status=409)\n';new='''    except ReviewConflict:
        if action == 'react':
            return render(request, 'catalog/review_reaction_conflict.html', {
                'review_reload_url': reverse('typed_reviews', args=[kind, target.pk]),
                'language': getattr(request, 'LANGUAGE_CODE', get_language()),
            }, status=409)
        return HttpResponse(status=409)
''';assert before.count(old)==1;after=before.replace(old,new)
html='''{% extends "base.html" %}
{% load static %}
{% block robots_meta %}noindex,follow{% endblock %}{% block googlebot_meta %}noindex,follow{% endblock %}
{% block extra_head %}<link rel="stylesheet" href="{% static 'css/pages/typed_reviews.css' %}">{% endblock %}
{% block title %}{% if language == 'ru' %}Отзыв изменился{% elif language == 'en' %}The review has changed{% else %}Rəy dəyişib{% endif %} — KidsMap{% endblock %}
{% block content %}
<div class="container typed-reviews km-page-content" data-review-reaction-conflict>
  <h1>{% if language == 'ru' %}Отзыв изменился{% elif language == 'en' %}The review has changed{% else %}Rəy dəyişib{% endif %}</h1>
  <p role="alert">{% if language == 'ru' %}Ваша реакция не сохранена: появилась новая редакция отзыва. Откройте актуальную страницу и решите, хотите ли вы проголосовать снова.{% elif language == 'en' %}Your reaction was not saved because the review has a new version. Open the latest page and decide whether to react again.{% else %}Rəyin yeni versiyası olduğu üçün reaksiyanız saxlanılmadı. Aktual səhifəni açın və yenidən səs verib-verməməyə qərar verin.{% endif %}</p>
  <p><a href="{{ review_reload_url }}" data-review-reaction-reload>{% if language == 'ru' %}Открыть актуальные отзывы{% elif language == 'en' %}Open the latest reviews{% else %}Aktual rəyləri aç{% endif %}</a></p>
</div>
{% endblock %}
'''
mapping={controller:after,template:html,test:(Q/'candidate_tests.py').read_text()};manifest={};diff=[]
for p,value in mapping.items():
 assert p==controller or not(R/p).exists()
 b=(R/p).read_text() if(R/p).exists() else ''
 target=O/'candidate'/p;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(value)
 manifest[p]={'before_sha256':sha(R/p) if(R/p).exists() else None,'candidate_sha256':sha(target)}
 diff.extend(difflib.unified_diff(b.splitlines(True),value.splitlines(True),fromfile='a/'+p if b else '/dev/null',tofile='b/'+p))
(O/'proposed-social12.diff').write_text(''.join(diff));(O/'candidate-manifest.json').write_text(json.dumps({'applied':False,'files':manifest,'diff_sha256':sha(O/'proposed-social12.diff'),'test_methods':4},indent=2));print(json.dumps({'candidate_files':list(mapping),'applied':False,'methods':4}))
