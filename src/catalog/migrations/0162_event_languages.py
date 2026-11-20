# Languages an event is held in ("az,ru"); shown on cards and used by the afisha filter.
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0161_event_slug_only_urls'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='languages',
            field=models.CharField(blank=True, db_default='', default='', max_length=32, verbose_name='Языки проведения'),
        ),
    ]
