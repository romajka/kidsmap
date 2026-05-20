from django.db import migrations, models


OLD_BAKU_DISTRICTS = [
    "Ясамал",
    "Насими",
    "Низами",
    "Нариманов",
    "Сабаиль",
    "Сабунчи",
    "Бинагади",
    "Сураханы",
    "Хатаи",
    "Хазар",
    "Гарадаг",
    "Пираллахы",
]

AZERBAIJAN_REGIONS = [
    "Баку",
    "Ясамал",
    "Насими",
    "Низами",
    "Нариманов",
    "Сабаиль",
    "Сабунчи",
    "Бинагади",
    "Сураханы",
    "Хатаи",
    "Хазар",
    "Гарадаг",
    "Пираллахы",
    "Абшерон",
    "Агджабеди",
    "Агдам",
    "Агдаш",
    "Агстафа",
    "Агсу",
    "Астара",
    "Бабек",
    "Балакен",
    "Барда",
    "Бейлаган",
    "Билясувар",
    "Габала",
    "Гаджикабул",
    "Газах",
    "Гах",
    "Гедабек",
    "Гянджа",
    "Гёйгёль",
    "Гёйчай",
    "Гобустан",
    "Горанбой",
    "Губа",
    "Губадлы",
    "Гусар",
    "Дашкесан",
    "Джебраил",
    "Джалилабад",
    "Джульфа",
    "Евлах",
    "Загатала",
    "Зангилан",
    "Зардаб",
    "Имишли",
    "Исмаиллы",
    "Кельбаджар",
    "Кенгерли",
    "Кюрдамир",
    "Лачин",
    "Ленкорань",
    "Лерик",
    "Масаллы",
    "Мингячевир",
    "Нахчыван",
    "Нафталан",
    "Нефтчала",
    "Огуз",
    "Ордубад",
    "Саатлы",
    "Сабирабад",
    "Садарак",
    "Сальян",
    "Самух",
    "Сиазань",
    "Сумгаит",
    "Тертер",
    "Товуз",
    "Уджар",
    "Физули",
    "Хачмаз",
    "Ходжавенд",
    "Ходжалы",
    "Хызы",
    "Шабран",
    "Шамахы",
    "Шамкир",
    "Шарур",
    "Шахбуз",
    "Шеки",
    "Ширван",
    "Шуша",
    "Ярдымлы",
]


SITE_TEXT_REPLACEMENTS = {
    "about_text_ru": {
        "old": "KidsMap — каталог детских кружков и секций в Баку.",
        "new": "KidsMap — каталог детских кружков и секций по Азербайджану.",
    },
    "about_text_en": {
        "old": "KidsMap is a catalog of kids clubs and courses in Baku.",
        "new": "KidsMap is a catalog of kids clubs and courses across Azerbaijan.",
    },
    "about_text_az": {
        "old": "KidsMap Bakıda uşaqlar üçün dərnək və kurs kataloqudur.",
        "new": "KidsMap Azərbaycanda uşaqlar üçün dərnək və kurs kataloqudur.",
    },
    "home_title_ru": {
        "old": "Найдите кружок для ребёнка в Баку",
        "new": "Найдите кружок для ребёнка в Азербайджане",
    },
    "home_title_en": {
        "old": "Find a club for your child in Baku",
        "new": "Find a club for your child in Azerbaijan",
    },
    "home_title_az": {
        "old": "Bakıda uşağınız üçün dərnək tapın",
        "new": "Azərbaycanda uşağınız üçün dərnək tapın",
    },
    "home_subtitle_ru": {
        "old": "Спорт, творчество, музыка, образование — всё в одном месте.",
        "new": "Спорт, творчество, музыка, образование по всем регионам — всё в одном месте.",
    },
    "home_subtitle_en": {
        "old": "Sports, creativity, music, and education in one place.",
        "new": "Sports, creativity, music, and education across all regions in one place.",
    },
    "home_subtitle_az": {
        "old": "İdman, yaradıcılıq, musiqi, təhsil — hamısı bir yerdə.",
        "new": "Bütün regionlarda idman, yaradıcılıq, musiqi və təhsil — hamısı bir yerdə.",
    },
}


def expand_catalog_defaults_to_azerbaijan(apps, schema_editor):
    SiteSettings = apps.get_model("catalog", "SiteSettings")
    CatalogContentSettings = apps.get_model("catalog", "CatalogContentSettings")

    site_settings = SiteSettings.objects.order_by("id").first()
    if site_settings:
        changed_fields = []
        for field_name, values in SITE_TEXT_REPLACEMENTS.items():
            current = (getattr(site_settings, field_name) or "").strip()
            if current in {"", values["old"]}:
                setattr(site_settings, field_name, values["new"])
                changed_fields.append(field_name)
        if changed_fields:
            site_settings.save(update_fields=[*changed_fields, "updated_at"])

    catalog_settings = CatalogContentSettings.objects.order_by("id").first()
    if catalog_settings:
        districts = catalog_settings.districts_json
        if not districts or districts == OLD_BAKU_DISTRICTS:
            catalog_settings.districts_json = AZERBAIJAN_REGIONS
            catalog_settings.save(update_fields=["districts_json", "updated_at"])


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0038_alter_funnelevent_event_type"),
    ]

    operations = [
        migrations.AlterField(
            model_name="catalogcontentsettings",
            name="districts_json",
            field=models.JSONField(blank=True, default=list, verbose_name="Регионы / районы (JSON)"),
        ),
        migrations.AlterField(
            model_name="place",
            name="district",
            field=models.CharField(blank=True, max_length=100, verbose_name="Регион / район"),
        ),
        migrations.RunPython(expand_catalog_defaults_to_azerbaijan, migrations.RunPython.noop),
    ]
