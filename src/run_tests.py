import os
import django
from django.conf import settings
from django.core.management import call_command

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()
    with open('scratch/test_out.txt', 'w') as f:
        call_command('test', 'catalog.testcases.public', verbosity=2, stdout=f, stderr=f)
