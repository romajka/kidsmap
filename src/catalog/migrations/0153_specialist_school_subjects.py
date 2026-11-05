from django.db import migrations


# Frozen data: never import the mutable runtime taxonomy into a migration.
SUBJECTS = (
    ('physics_tutor', 'Репетитор по физике', 'Fizika repetitoru', 'Physics tutor'),
    ('chemistry_tutor', 'Репетитор по химии', 'Kimya repetitoru', 'Chemistry tutor'),
    ('biology_tutor', 'Репетитор по биологии', 'Biologiya repetitoru', 'Biology tutor'),
    ('history_tutor', 'Репетитор по истории', 'Tarix repetitoru', 'History tutor'),
    ('geography_tutor', 'Репетитор по географии', 'Coğrafiya repetitoru', 'Geography tutor'),
    ('informatics_tutor', 'Репетитор по информатике', 'İnformatika repetitoru', 'Computer science tutor'),
    ('french_teacher', 'Преподаватель французского языка', 'Fransız dili müəllimi', 'French teacher'),
    ('german_teacher', 'Преподаватель немецкого языка', 'Alman dili müəllimi', 'German teacher'),
)


def seed_subjects(apps, schema_editor):
    model = apps.get_model('catalog', 'SpecialistSpecialization')
    for order, (code, ru, az, en) in enumerate(SUBJECTS, 81):
        model.objects.using(schema_editor.connection.alias).get_or_create(
            code=code, defaults={'name': en, 'name_ru': ru, 'name_az': az,
                                 'name_en': en, 'order': order, 'is_active': True})


class Migration(migrations.Migration):
    dependencies = [('catalog', '0152_place_clean_public_urls')]
    # Preserve referenced choices on rollback; no schema or existing profile changes.
    operations = [migrations.RunPython(seed_subjects, migrations.RunPython.noop)]
