from django.db import migrations


PLACE_COORDINATES = {
    "Детский футбольный клуб Габала": (40.9814, 47.8455),
    "Академия робототехники Сумгаит": (40.5897, 49.6685),
    "Шекинская школа искусств": (41.1987, 47.1706),
    "Спортивный клуб Губа": (41.3611, 48.5134),
    "Центр развития Гянджа": (40.6828, 46.3606),
    "Ленкоранский шахматный кружок": (38.7529, 48.8515),
    "Шамахинская музыкальная студия": (40.6314, 48.6414),
}


def fix_coordinates(apps, schema_editor):
    Place = apps.get_model("catalog", "Place")
    for name, (lat, lng) in PLACE_COORDINATES.items():
        Place.objects.filter(name=name).update(lat=lat, lng=lng)


class Migration(migrations.Migration):
    dependencies = [("catalog", "0069_place_multilingual_extra_fields")]

    operations = [migrations.RunPython(fix_coordinates, migrations.RunPython.noop)]
