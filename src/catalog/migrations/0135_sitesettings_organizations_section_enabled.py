from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('catalog', '0134_completion_taxonomy')]
    operations = [
        migrations.AddField(
            model_name='sitesettings', name='organizations_section_enabled',
            field=models.BooleanField(default=True, verbose_name='Показывать «Организации»', help_text='Скрывает каталог организаций, их публичные страницы и блоки со ссылками на организации. Филиалы, данные, админка и кабинет организаций остаются доступны.'),
        ),
        migrations.AlterField(
            model_name='sitesettings', name='events_section_enabled',
            field=models.BooleanField(default=True, verbose_name='Показывать «Афишу»', help_text='Скрывает афишу, временные карточки, ссылки на них и добавление мероприятий в личном кабинете. Записи и их редактирование в админке сохраняются.'),
        ),
        migrations.AlterField(
            model_name='sitesettings', name='specialists_section_enabled',
            field=models.BooleanField(default=True, verbose_name='Показывать «Педагогов и специалистов»', help_text='Скрывает каталог специалистов, ссылки на него и добавление специалистов в личном кабинете. Записи и их редактирование в админке сохраняются.'),
        ),
    ]
