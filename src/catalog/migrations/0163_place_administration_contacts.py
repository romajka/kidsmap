from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('catalog', '0162_event_languages')]

    operations = [
        migrations.AddField(
            model_name='place',
            name='administration_name',
            field=models.CharField(blank=True, db_default='', default='', max_length=255,
                                   verbose_name='Ответственная организация'),
        ),
        migrations.AddField(
            model_name='place',
            name='administration_phone',
            field=models.CharField(blank=True, db_default='', default='', max_length=50,
                                   verbose_name='Официальный телефон организации'),
        ),
    ]
