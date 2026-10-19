from django.contrib.auth import get_user_model

def seed():
 U=get_user_model();assert not U.objects.filter(username='s08-fix-outsider').exists();U.objects.create_user('s08-fix-outsider',email='outsider-fix@example.invalid');print('Own outsider fictional guard user created')
