from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('catalog', '0126_task33_volunteer_review_status'), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(name='WorkflowNotification', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('event_kind', models.CharField(max_length=48)),
            ('entity_type', models.CharField(max_length=48)),
            ('entity_id', models.PositiveBigIntegerField()),
            ('entity_version', models.PositiveBigIntegerField()),
            ('recipient_key', models.CharField(max_length=80)),
            ('recipient_email', models.EmailField(blank=True, default='', max_length=254)),
            ('read_at', models.DateTimeField(blank=True, null=True)),
            ('created_at', models.DateTimeField(auto_now_add=True)),
            ('recipient_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='workflow_notifications', to=settings.AUTH_USER_MODEL)),
        ], options={
            'indexes': [models.Index(fields=['recipient_user', '-created_at'], name='workflow_inbox_user_created')],
            'constraints': [
                models.UniqueConstraint(fields=['event_kind', 'entity_type', 'entity_id', 'entity_version', 'recipient_key'], name='workflow_event_recipient_unique'),
                models.CheckConstraint(condition=models.Q(entity_id__gte=1, entity_version__gte=1), name='workflow_event_positive_identity'),
            ],
        }),
        migrations.CreateModel(name='EmailOutbox', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('recipient_email', models.EmailField(max_length=254)),
            ('status', models.CharField(choices=[('pending', 'Pending'), ('retry', 'Retry'), ('sent', 'Sent'), ('suppressed', 'Suppressed'), ('failed', 'Failed')], db_index=True, default='pending', max_length=16)),
            ('attempts', models.PositiveSmallIntegerField(default=0)),
            ('next_attempt_at', models.DateTimeField(blank=True, null=True)),
            ('sent_at', models.DateTimeField(blank=True, null=True)),
            ('last_error_code', models.CharField(blank=True, default='', max_length=32)),
            ('created_at', models.DateTimeField(auto_now_add=True)),
            ('updated_at', models.DateTimeField(auto_now=True)),
            ('notification', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE,
                related_name='email_outbox', to='catalog.workflownotification')),
        ], options={
            'indexes': [models.Index(fields=['status', 'next_attempt_at', 'id'], name='workflow_outbox_due')],
            'constraints': [models.CheckConstraint(condition=models.Q(attempts__lte=5), name='workflow_outbox_attempt_cap')],
        }),
    ]
