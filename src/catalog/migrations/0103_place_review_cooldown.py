from datetime import timedelta

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


def seed_cooldowns(apps, schema_editor):
    Review = apps.get_model('catalog', 'PlaceReview')
    Cooldown = apps.get_model('catalog', 'PlaceReviewCooldown')
    alias = schema_editor.connection.alias
    rows = Review.objects.using(alias).exclude(user_id=None).values('place_id', 'user_id').annotate(latest=models.Max('created_at'))
    batch = []
    for row in rows.iterator(chunk_size=500):
        batch.append(Cooldown(place_id=row['place_id'], user_id=row['user_id'], next_allowed_at=row['latest'] + timedelta(seconds=120)))
        if len(batch) == 500:
            Cooldown.objects.using(alias).bulk_create(batch)
            batch = []
    Cooldown.objects.using(alias).bulk_create(batch)


class Migration(migrations.Migration):
    dependencies = [
        ('catalog', '0102_volunteer_place_revision'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
    operations = [
        migrations.CreateModel(
            name='PlaceReviewCooldown',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('next_allowed_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('place', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='catalog.place')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={'constraints': [models.UniqueConstraint(fields=('place', 'user'), name='unique_place_review_cooldown')]},
        ),
        migrations.RunPython(seed_cooldowns, migrations.RunPython.noop),
        migrations.RemoveConstraint(model_name='placereview', name='unique_place_review_per_user'),
        migrations.AddIndex(model_name='placereview', index=models.Index(fields=['place', 'user', '-created_at'], name='review_place_user_latest')),
    ]
