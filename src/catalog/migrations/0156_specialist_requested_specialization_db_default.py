from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0155_specialist_requested_specialization'),
    ]

    operations = [
        migrations.AlterField(
            model_name='specialist',
            name='requested_specialization',
            field=models.CharField(blank=True, db_default='', default='', help_text='Направление, которого нет в списке. Модератор может добавить его в справочник и отметить в анкете.', max_length=120, verbose_name='Предложенное направление'),
        ),
    ]
