from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('catalog', '0144_workflownotification_event_context_db_default')]
    operations = [
        migrations.AddField(model_name='place', name='phone_country',
                            field=models.CharField(default='AZ', db_default='AZ', max_length=2, verbose_name='Страна номера')),
        migrations.AddField(model_name='place', name='whatsapp_mode',
                            field=models.CharField(default='legacy', db_default='legacy', max_length=10, verbose_name='WhatsApp', choices=[
                                ('legacy', 'Совместимость со старой карточкой'),
                                ('same', 'WhatsApp совпадает с телефоном'),
                                ('separate', 'Отдельный номер WhatsApp'),
                                ('none', 'WhatsApp отсутствует')])),
        migrations.AddField(model_name='place', name='whatsapp_number',
                            field=models.CharField(blank=True, default='', db_default='', max_length=50, verbose_name='Номер WhatsApp')),
    ]
