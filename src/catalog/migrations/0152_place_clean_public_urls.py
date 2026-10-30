"""Existing rows and old-image INSERTs keep their numeric public URLs."""
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('catalog', '0151_place_age_varies_by_program')]

    operations = [
        migrations.AddField(
            model_name='place', name='uses_slug_only_urls',
            field=models.BooleanField(default=True, db_default=False, editable=False),
        ),
        *[
            migrations.AddField(
                model_name='place', name=f'public_slug_{language}',
                field=models.SlugField(max_length=60, null=True, blank=True, unique=True, editable=False),
            )
            for language in ('az', 'ru', 'en')
        ],
    ]
