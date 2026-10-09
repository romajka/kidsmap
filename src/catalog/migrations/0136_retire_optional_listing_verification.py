from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('catalog', '0135_sitesettings_organizations_section_enabled')]
    operations = [
        migrations.AlterField(model_name='place', name='is_verified', field=models.BooleanField(default=False, editable=False, verbose_name='Проверено')),
        migrations.AlterField(model_name='specialist', name='is_verified', field=models.BooleanField(default=False, editable=False, verbose_name='Проверен')),
    ]
