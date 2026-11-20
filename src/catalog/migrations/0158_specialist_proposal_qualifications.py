import catalog.private_storage
import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0157_specialist_session_formats'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='specialistdocument',
            name='uploaded_by',
            field=models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='specialistdocument',
            name='verified_at_upload',
            field=models.DateTimeField(blank=True, editable=False, null=True),
        ),
        migrations.CreateModel(
            name='SpecialistProposalDocument',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('document_type', models.CharField(choices=[('diploma', 'Диплом'), ('certificate', 'Сертификат')], max_length=20)),
                ('file', models.FileField(storage=catalog.private_storage.SpecialistPrivateStorage(), upload_to=catalog.private_storage.specialist_document_path)),
                ('publish', models.BooleanField(default=False)),
                ('opted_in_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('draft', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='qualification_documents', to='catalog.specialistproposaldraft')),
            ],
            options={
                'ordering': ['created_at', 'pk'],
            },
        ),
    ]
