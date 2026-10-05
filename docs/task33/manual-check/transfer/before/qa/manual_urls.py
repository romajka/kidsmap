import json,mimetypes,html as html_module
from pathlib import Path
from django.conf import settings
from django.contrib.auth import login,logout,get_user_model
from django.http import HttpResponse,JsonResponse,FileResponse,Http404
from django.middleware.csrf import get_token
from django.shortcuts import redirect
from django.urls import path
from django.views.decorators.http import require_POST
from config.urls import urlpatterns as application_urls

HERE=Path(__file__).resolve().parents[1]

def guide(request):
    html=(HERE/'guide.html').read_text(encoding='utf-8')
    html=html.replace('__CSRF__',get_token(request)).replace('__CURRENT_ROLE__',html_module.escape(request.user.username) if request.user.is_authenticated else 'Гость')
    return HttpResponse(html)

def fixtures(request):
    return JsonResponse(json.loads((settings.QA_ROOT/'fixtures.json').read_text()))

@require_POST
def session(request):
    role=request.POST.get('role','')
    if role=='guest':logout(request)
    elif role in ('parent','owner','manager','person','moderator','outsider','volunteer'):
        login(request,get_user_model().objects.get(username='demo_'+role),backend='django.contrib.auth.backends.ModelBackend')
    else:raise Http404
    return redirect('/qa/')

def document(request,area,filename):
    roots={'screens':HERE/'screenshots','report':HERE.parent/'completion','final-audit':HERE.parent/'final-audit'}
    if area not in roots:raise Http404
    if area=='final-audit' and filename not in ('REPORT.md','REQUIREMENTS.md'):raise Http404
    root=roots[area].resolve();target=(root/filename).resolve()
    if not target.is_relative_to(root) or not target.is_file() or target.suffix not in ('.html','.json','.png','.md','.log'):raise Http404
    return FileResponse(target.open('rb'),content_type=mimetypes.guess_type(target.name)[0] or 'application/octet-stream')

urlpatterns=[path('qa/',guide),path('qa/fixtures.json',fixtures),path('qa/login/',session),
    path('qa/files/<str:area>/<path:filename>',document)]+application_urls
