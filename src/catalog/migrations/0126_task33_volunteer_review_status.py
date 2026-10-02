from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('catalog', '0125_task33_group_conditions_verified')]
    operations = [migrations.AlterField(
        model_name='volunteerplacerevision', name='status',
        field=models.CharField(max_length=16, db_index=True, default='draft', choices=[
            ('draft', 'Черновик'), ('pending', 'На проверке'),
            ('approved', 'Одобрено'), ('rejected', 'Нужны исправления'),
            ('declined', 'Отклонено'),
        ]),
    )]
