from django.db import migrations, models

from catalog.services.event_slugs import available_event_slug, event_slug_base


def reserve_event_slugs(apps, schema_editor):
    connection = schema_editor.connection
    events = apps.get_model('catalog', 'Event').objects.using(connection.alias)
    if connection.vendor == 'postgresql':
        # Keep the inventory stable until the unique index is installed.
        schema_editor.execute('LOCK TABLE catalog_event IN SHARE ROW EXCLUSIVE MODE')
        schema_editor.execute('SET CONSTRAINTS ALL IMMEDIATE')

    used = set()
    pending = []
    rows = events.order_by('pk').values_list('pk', 'slug', 'name_az', 'name_ru', 'name_en', 'name')
    for pk, slug, *names in rows.iterator():
        base = event_slug_base(slug or next((name for name in names if name), ''))
        if slug == base and base not in used:
            used.add(base)
        else:
            pending.append((pk, base))

    # Protect existing readable names before allocating replacements to collisions.
    for pk, base in pending:
        slug = available_event_slug(base, used.__contains__)
        events.filter(pk=pk).update(slug=slug)
        used.add(slug)


class Migration(migrations.Migration):
    dependencies = [('catalog', '0160_preserve_hidden_replies_on_rollback')]
    operations = [
        migrations.RunPython(reserve_event_slugs, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='event', name='slug',
            field=models.SlugField(blank=True, default='', max_length=255, unique=True, verbose_name='Slug'),
        ),
    ]
