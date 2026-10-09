from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [('catalog', '0140_specialist_proposal_draft')]

    # Record existing admin labels in migration state; no schema or data changes.
    operations = [
        migrations.AlterModelOptions(
            name='activity',
            options={'verbose_name': 'Направление', 'verbose_name_plural': 'Направления'},
        ),
        migrations.AlterModelOptions(
            name='offeringgroup',
            options={'verbose_name': 'Группа занятий', 'verbose_name_plural': 'Группы занятий'},
        ),
        migrations.AlterModelOptions(
            name='organization',
            options={'verbose_name': 'Организация', 'verbose_name_plural': 'Организации'},
        ),
        migrations.AlterModelOptions(
            name='program',
            options={'verbose_name': 'Программа', 'verbose_name_plural': 'Программы'},
        ),
    ]
