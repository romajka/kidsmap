from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('catalog', '0112_ratingrankingcalibration')]

    operations = [
        migrations.AddField(
            model_name='place', name=f'slug_{language}',
            field=models.SlugField(blank=True, default='', editable=False, max_length=60, verbose_name=f'URL {language.upper()}'),
        )
        for language in ('az', 'ru', 'en')
    ]
