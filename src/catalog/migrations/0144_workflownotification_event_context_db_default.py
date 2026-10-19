"""Keep notification INSERTs from pre-0142 workers compatible with the schema."""
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('catalog', '0143_pending_email_change')]

    operations = [
        migrations.AlterField(
            model_name='workflownotification', name='event_context',
            field=models.JSONField(blank=True, default=dict, db_default={}),
        ),
    ]
