from django.contrib.auth import get_user_model
from django.db import transaction
from catalog.models import SiteReview

def seed():
    with transaction.atomic():
        U=get_user_model()
        assert not U.objects.exists()
        U.objects.create_user('s05-author',email='author@example.invalid',first_name='Fictional')
        for i,rating in enumerate([4,5]):
            u=U.objects.create_user('s05-reviewer-'+str(i),email='reviewer'+str(i)+'@example.invalid',first_name='Fictional')
            SiteReview.objects.create(user=u,author_name='Fictional reviewer '+str(i),rating=rating,
                text='Fictional review for isolated layout QA.',status='approved',is_approved=True,likes_count=i)
    print('Seeded own author and two approved fictional reviews; no delivery/external services')
