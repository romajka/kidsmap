from django.db import migrations


SPECIALIZATIONS = [
    ("tutor", "Tutor", "Репетитор", "Repetitor", "Tutor", 10),
    ("primary_teacher", "Primary school teacher", "Учитель начальных классов", "İbtidai sinif müəllimi", "Primary school teacher", 20),
    ("school_prep_teacher", "School preparation educator", "Подготовка к школе", "Məktəbə hazırlıq müəllimi", "School preparation educator", 30),
    ("english_teacher", "English teacher", "Преподаватель английского языка", "İngilis dili müəllimi", "English teacher", 40),
    ("russian_teacher", "Russian teacher", "Преподаватель русского языка", "Rus dili müəllimi", "Russian teacher", 50),
    ("azerbaijani_teacher", "Azerbaijani teacher", "Преподаватель азербайджанского языка", "Azərbaycan dili müəllimi", "Azerbaijani teacher", 60),
    ("math_tutor", "Math tutor", "Репетитор по математике", "Riyaziyyat repetitoru", "Math tutor", 70),
    ("exam_prep_tutor", "Exam preparation tutor", "Подготовка к экзаменам", "İmtahanlara hazırlıq repetitoru", "Exam preparation tutor", 80),
    ("child_psychologist", "Child psychologist", "Детский психолог", "Uşaq psixoloqu", "Child psychologist", 110),
    ("sports_psychologist", "Sports psychologist", "Спортивный психолог", "İdman psixoloqu", "Sports psychologist", 120),
    ("early_development_specialist", "Early development specialist", "Специалист по раннему развитию", "Erkən inkişaf mütəxəssisi", "Early development specialist", 150),
    ("career_guidance_specialist", "Career guidance specialist", "Профориентолог", "Peşəyönümü mütəxəssisi", "Career guidance specialist", 170),
    ("personal_trainer", "Personal trainer", "Персональный тренер", "Fərdi məşqçi", "Personal trainer", 210),
    ("sports_coach", "Sports coach", "Тренер по виду спорта", "İdman növü üzrə məşqçi", "Sports coach", 220),
    ("posture_correction_specialist", "Posture correction specialist", "Специалист по коррекции осанки", "Qamət korreksiyası mütəxəssisi", "Posture correction specialist", 230),
    ("physical_rehab_specialist", "Physical rehabilitation specialist", "Специалист по физической реабилитации", "Fiziki reabilitasiya mütəxəssisi", "Physical rehabilitation specialist", 250),
    ("music_teacher", "Music teacher", "Преподаватель музыки", "Musiqi müəllimi", "Music teacher", 310),
    ("drawing_teacher", "Drawing teacher", "Преподаватель рисования", "Rəsm müəllimi", "Drawing teacher", 320),
    ("acting_teacher", "Acting teacher", "Преподаватель актёрского мастерства", "Aktyorluq müəllimi", "Acting teacher", 330),
    ("programming_mentor", "Programming mentor", "Наставник по программированию", "Proqramlaşdırma mentoru", "Programming mentor", 340),
    ("robotics_teacher", "Robotics teacher", "Преподаватель робототехники", "Robototexnika müəllimi", "Robotics teacher", 350),
]


def seed_specializations(apps, schema_editor):
    SpecialistSpecialization = apps.get_model("catalog", "SpecialistSpecialization")
    for code, name, name_ru, name_az, name_en, order in SPECIALIZATIONS:
        obj, created = SpecialistSpecialization.objects.get_or_create(
            code=code,
            defaults={
                "name": name,
                "name_ru": name_ru,
                "name_az": name_az,
                "name_en": name_en,
                "is_active": True,
                "order": order,
            },
        )
        if not created:
            changed = False
            for field, value in {
                "name": name,
                "name_ru": name_ru,
                "name_az": name_az,
                "name_en": name_en,
                "is_active": True,
            }.items():
                if getattr(obj, field) != value:
                    setattr(obj, field, value)
                    changed = True
            if not obj.order:
                obj.order = order
                changed = True
            if changed:
                obj.save(update_fields=["name", "name_ru", "name_az", "name_en", "is_active", "order"])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0058_alter_place_options"),
    ]

    operations = [
        migrations.RunPython(seed_specializations, noop_reverse),
    ]
