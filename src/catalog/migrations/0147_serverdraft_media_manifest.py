from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('catalog', '0146_place_public_links')]
    operations = [migrations.AddField(
        model_name='serverdraft', name='media_manifest',
        field=models.JSONField(blank=True, default=list),
    )]
