"""Keep pre-release place and draft INSERTs compatible during image rollback."""
from django.db import migrations, models
import catalog.services.place_public_links


class Migration(migrations.Migration):
    dependencies = [('catalog', '0147_serverdraft_media_manifest')]

    operations = [
        migrations.AlterField(
            model_name='place', name='public_links',
            field=models.JSONField(
                blank=True, default=list, db_default=[],
                validators=[catalog.services.place_public_links.validate_public_links],
                verbose_name='Дополнительные ссылки',
            ),
        ),
        migrations.AlterField(
            model_name='serverdraft', name='media_manifest',
            field=models.JSONField(blank=True, default=list, db_default=[]),
        ),
    ]
