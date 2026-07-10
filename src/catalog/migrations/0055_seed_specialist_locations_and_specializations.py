from django.db import migrations
from django.utils.translation import activate
from django.utils.text import slugify

# We import the exact maps and lists
from catalog.services.locations import AZERBAIJAN_REGIONS_MAP, BAKU_DISTRICTS_MAP
from catalog.content_data import BAKU_METRO_STATIONS

SPECIALIZATIONS = [
    {
        "code": "psychologist",
        "name": "Psychologist",
        "name_ru": "Психолог",
        "name_az": "Psixoloq",
        "name_en": "Psychologist",
    },
    {
        "code": "speech_therapist",
        "name": "Speech Therapist",
        "name_ru": "Логопед",
        "name_az": "Loqoped",
        "name_en": "Speech Therapist",
    },
    {
        "code": "pathologist",
        "name": "Pathologist/Special Educator",
        "name_ru": "Дефектолог",
        "name_az": "Defektoloq",
        "name_en": "Defectologist",
    },
    {
        "code": "physiotherapist",
        "name": "Physiotherapist",
        "name_ru": "Физиотерапевт",
        "name_az": "Fizioterapevt",
        "name_en": "Physiotherapist",
    },
    {
        "code": "rehab_specialist",
        "name": "Rehabilitation Specialist",
        "name_ru": "Реабилитолог",
        "name_az": "Reabilitoloq",
        "name_en": "Rehabilitation Specialist",
    },
    {
        "code": "sensory_integration",
        "name": "Sensory Integration Specialist",
        "name_ru": "Специалист по сенсорной интеграции",
        "name_az": "Sensor inteqrasiya mütəxəssisi",
        "name_en": "Sensory Integration Specialist",
    },
    {
        "code": "neuropediatrician",
        "name": "Neuropediatrician",
        "name_ru": "Детский невролог",
        "name_az": "Uşaq nevroloqu",
        "name_en": "Neuropediatrician",
    },
    {
        "code": "pediatrician",
        "name": "Pediatrician",
        "name_ru": "Педиатр",
        "name_az": "Pediatr",
        "name_en": "Pediatrician",
    },
]

def seed_data(apps, schema_editor):
    Region = apps.get_model("catalog", "Region")
    District = apps.get_model("catalog", "District")
    MetroStation = apps.get_model("catalog", "MetroStation")
    SpecialistSpecialization = apps.get_model("catalog", "SpecialistSpecialization")

    # 1. Regions
    for key, val in AZERBAIJAN_REGIONS_MAP.items():
        Region.objects.get_or_create(
            key=key,
            defaults={
                "name_ru": val["ru"],
                "name_az": val["az"],
                "name_en": val["en"]
            }
        )

    # 2. Districts (belong to Baku)
    baku_region, _ = Region.objects.get_or_create(
        key="baku",
        defaults={
            "name_ru": "Баку",
            "name_az": "Bakı",
            "name_en": "Baku"
        }
    )
    for key, val in BAKU_DISTRICTS_MAP.items():
        District.objects.get_or_create(
            key=key,
            defaults={
                "region": baku_region,
                "name_ru": val["ru"],
                "name_az": val["az"],
                "name_en": val["en"]
            }
        )

    # 3. Metro Stations
    from django.utils.translation import gettext as _
    for idx, station_name in enumerate(BAKU_METRO_STATIONS):
        # Resolve lazy gettext by activating languages to capture compiled translations
        original_name = str(station_name)
        
        activate("ru")
        name_ru = _(original_name)
        activate("az")
        name_az = _(original_name)
        activate("en")
        name_en = _(original_name)
        activate("az") # Reset default

        key = slugify(name_en) or f"metro_{idx}"
        MetroStation.objects.get_or_create(
            key=key,
            defaults={
                "name_ru": name_ru,
                "name_az": name_az,
                "name_en": name_en
            }
        )

    # 4. Specializations
    for spec in SPECIALIZATIONS:
        SpecialistSpecialization.objects.get_or_create(
            code=spec["code"],
            defaults={
                "name": spec["name"],
                "name_ru": spec["name_ru"],
                "name_az": spec["name_az"],
                "name_en": spec["name_en"]
            }
        )

def rollback_data(apps, schema_editor):
    Region = apps.get_model("catalog", "Region")
    District = apps.get_model("catalog", "District")
    MetroStation = apps.get_model("catalog", "MetroStation")
    SpecialistSpecialization = apps.get_model("catalog", "SpecialistSpecialization")

    SpecialistSpecialization.objects.all().delete()
    MetroStation.objects.all().delete()
    District.objects.all().delete()
    Region.objects.all().delete()

class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0054_metrostation_region_specialistspecialization_and_more"),
    ]
    operations = [
        migrations.RunPython(seed_data, rollback_data),
    ]
