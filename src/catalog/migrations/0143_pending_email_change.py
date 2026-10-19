import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('catalog', '0142_workflownotification_event_context'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PendingEmailChange',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('source_email', models.EmailField(blank=True, default='', max_length=254)),
                ('email', models.EmailField(blank=True, default='', max_length=254)),
                ('token', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('code_hash', models.CharField(blank=True, default='', max_length=255)),
                ('expires_at', models.DateTimeField(blank=True, null=True)),
                ('resend_available_at', models.DateTimeField(blank=True, null=True)),
                ('attempts_left', models.PositiveSmallIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE,
                                             related_name='pending_email_change', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
