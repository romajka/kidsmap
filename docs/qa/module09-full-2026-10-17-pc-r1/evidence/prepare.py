from pathlib import Path
Q=Path(__file__).resolve().parent;R=Q.parents[1]
t=(R/'docs/qa/module09-2026-10-10-r1/qa_urls.py').read_text()
a=t.index('def version(');b=t.index('def state(');t=t[:a]+t[b:]
t=t.replace("assert settings.TESTING and request.META['REMOTE_ADDR'] in ['127.0.0.1','::1']","assert settings.TESTING and settings.DATABASES['default']['NAME']=='m09full_r1'")
t=t[:t.index('urlpatterns=')]+'''def fixture_login(request,role):
 from django.contrib.auth import login,logout,get_user_model
 from django.shortcuts import redirect
 assert role in ['guest','author','owner','employee','outsider','moderator','staff','admin','empty','invitee']
 if role=='guest':logout(request)
 else:login(request,get_user_model().objects.get(username='qa09_'+role),backend='django.contrib.auth.backends.ModelBackend')
 return redirect('site_reviews')
urlpatterns=[path('qa/login/<str:role>/',fixture_login),path('qa/state/',state)]+application
'''
(Q/'qa_urls.py').write_text(t)
labels=['test_task33_reviews','test_task33_review_independent','test_review_confirmation','test_place_review_cooldown','test_favorite_metrics','test_public_favorite_count','test_task33_notifications','test_task33_notification_crashes','test_social_qa01_rating_readback','test_social_qa02_rejection_feedback','test_social_qa03_conflict_recovery','test_social_qa07_activity_review_title','test_social_qa08_invitation_feedback','test_social_qa09_feed_query','public.TestReviewEnhancements','admin.ReviewAdminModerationTests','admin.TestReviewRatingSyncAndAdminBulkActions','catalog.ContentModerationPublicVisibilityTests']
args=['catalog.testcases.'+x for x in labels];(Q/'test-labels.json').write_text(__import__('json').dumps(args,indent=2))
(Q/'tests.sh').write_text('''#!/bin/sh
qa=/mnt/c/kidsmap/.tmp/module09-full-pc-r1
docker exec m09full-r1-app python "$qa/runtime.py" test '''+' '.join(args)+''' > "$qa/tests.log" 2>&1
result=$?
printf '%s\\n' "$result" > "$qa/tests.exit"
tail -n 14 "$qa/tests.log"
exit "$result"
''')
print('Fresh full module corpus prepared',len(args),'labels; migration test old hardcoded socket excluded and documented')
