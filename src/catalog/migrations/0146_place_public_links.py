from django.db import migrations, models
import catalog.services.place_public_links


class Migration(migrations.Migration):
    dependencies=[('catalog','0145_place_phone_whatsapp')]
    operations=[migrations.AddField(model_name='place',name='public_links',field=models.JSONField(blank=True,default=list,validators=[catalog.services.place_public_links.validate_public_links],verbose_name='Дополнительные ссылки'))]
