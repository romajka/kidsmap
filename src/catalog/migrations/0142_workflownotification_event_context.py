from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('catalog', '0141_catalog_admin_names')]

    operations = [
        migrations.AddField(
            model_name='workflownotification',
            name='event_context',
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
