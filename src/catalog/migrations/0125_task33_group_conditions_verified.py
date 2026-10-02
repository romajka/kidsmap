from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [('catalog', '0124_task33_conversion')]
    operations = [migrations.RenameField(
        model_name='offeringgroup', old_name='conditions_confirmed_at', new_name='conditions_verified_at')]
