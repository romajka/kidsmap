"""Receipts must not introduce a new veto on the existing user purge."""
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('catalog','0138_business_role_labels'),migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [migrations.AlterField(model_name='organizationconnectionoperation',name='actor',
        field=models.ForeignKey(null=True,on_delete=models.SET_NULL,to=settings.AUTH_USER_MODEL))]
