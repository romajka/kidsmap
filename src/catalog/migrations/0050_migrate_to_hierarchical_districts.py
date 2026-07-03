from django.db import migrations

AZERBAIJAN_REGIONS_MAP = {
    "absheron": {"ru": "Абшерон", "az": "Abşeron", "en": "Absheron"},
    "agdjabedi": {"ru": "Агджабеди", "az": "Ağcabədi", "en": "Agdjabedi"},
    "agdam": {"ru": "Агдам", "az": "Ağdam", "en": "Agdam"},
    "agdash": {"ru": "Агдаш", "az": "Ağdaş", "en": "Agdash"},
    "agstafa": {"ru": "Агстафа", "az": "Ağstafa", "en": "Agstafa"},
    "agsu": {"ru": "Агсу", "az": "Ağsu", "en": "Agsu"},
    "astara": {"ru": "Астара", "az": "Astara", "en": "Astara"},
    "babek": {"ru": "Бабек", "az": "Babək", "en": "Babek"},
    "balaken": {"ru": "Балакен", "az": "Balakən", "en": "Balaken"},
    "barda": {"ru": "Барда", "az": "Bərdə", "en": "Barda"},
    "beylagan": {"ru": "Бейлаган", "az": "Beyləqan", "en": "Beylagan"},
    "bilyasuvar": {"ru": "Билясувар", "az": "Biləsuvar", "en": "Bilyasuvar"},
    "gabala": {"ru": "Габала", "az": "Qəbələ", "en": "Gabala"},
    "hadjigabul": {"ru": "Гаджикабул", "az": "Hacıqabul", "en": "Hadjigabul"},
    "gazakh": {"ru": "Газах", "az": "Qazax", "en": "Gazakh"},
    "gakh": {"ru": "Гах", "az": "Qax", "en": "Gakh"},
    "gedabek": {"ru": "Гедабек", "az": "Gədəbəy", "en": "Gedabek"},
    "ganja": {"ru": "Гянджа", "az": "Gəncə", "en": "Ganja"},
    "goygol": {"ru": "Гёйгёль", "az": "Göygöl", "en": "Goygol"},
    "goychay": {"ru": "Гёйчай", "az": "Göyçay", "en": "Goychay"},
    "gobustan": {"ru": "Гобустан", "az": "Qobustan", "en": "Gobustan"},
    "goranboy": {"ru": "Горанбой", "az": "Goranboy", "en": "Goranboy"},
    "guba": {"ru": "Губа", "az": "Quba", "en": "Guba"},
    "gubadly": {"ru": "Губадлы", "az": "Qubadlı", "en": "Gubadly"},
    "gusar": {"ru": "Гусар", "az": "Qusar", "en": "Gusar"},
    "dashkasan": {"ru": "Дашкесан", "az": "Daşkəsən", "en": "Dashkasan"},
    "djabrayil": {"ru": "Джебраил", "az": "Cəbrayıl", "en": "Djabrayil"},
    "djalilabad": {"ru": "Джалилабад", "az": "Cəlilabad", "en": "Djalilabad"},
    "djulfa": {"ru": "Джульфа", "az": "Culfa", "en": "Djulfa"},
    "yevlakh": {"ru": "Евлах", "az": "Yevlax", "en": "Yevlakh"},
    "zagatala": {"ru": "Загатала", "az": "Zaqatala", "en": "Zagatala"},
    "zangilan": {"ru": "Зангилан", "az": "Zəngilan", "en": "Zangilan"},
    "zardab": {"ru": "Зардаб", "az": "Zərdab", "en": "Zardab"},
    "imishli": {"ru": "Имишли", "az": "İmişli", "en": "Imishli"},
    "ismailly": {"ru": "Исмаиллы", "az": "İsmayıllı", "en": "Ismailly"},
    "kelbadjar": {"ru": "Кельбаджар", "az": "Kəlbəcər", "en": "Kelbadjar"},
    "kengerli": {"ru": "Кенгерли", "az": "Kəngərli", "en": "Kengerli"},
    "kurdamir": {"ru": "Кюрдамир", "az": "Kürdəmir", "en": "Kurdamir"},
    "lachin": {"ru": "Лачин", "az": "Laçın", "en": "Lachin"},
    "lankaran": {"ru": "Ленкорань", "az": "Lənkəran", "en": "Lankaran"},
    "lerik": {"ru": "Лерик", "az": "Lerik", "en": "Lerik"},
    "masalli": {"ru": "Масаллы", "az": "Masallı", "en": "Masalli"},
    "mingachevir": {"ru": "Мингячевир", "az": "Mingəçevir", "en": "Mingachevir"},
    "nakhchivan": {"ru": "Нахчыван", "az": "Naxçıvan", "en": "Nakhchivan"},
    "naftalan": {"ru": "Нафталан", "az": "Naftalan", "en": "Naftalan"},
    "neftchala": {"ru": "Нефтчала", "az": "Neftçala", "en": "Neftchala"},
    "oguz": {"ru": "Огуз", "az": "Oğuz", "en": "Oguz"},
    "ordubad": {"ru": "Ордубад", "az": "Ordubad", "en": "Ordubad"},
    "saatly": {"ru": "Саатлы", "az": "Saatlı", "en": "Saatly"},
    "sabirabad": {"ru": "Сабирабад", "az": "Sabirabad", "en": "Sabirabad"},
    "sadarak": {"ru": "Садарак", "az": "Sədərək", "en": "Sadarak"},
    "salyan": {"ru": "Сальян", "az": "Salyan", "en": "Salyan"},
    "samukh": {"ru": "Самух", "az": "Samux", "en": "Samukh"},
    "siyazan": {"ru": "Сиазань", "az": "Siyəzən", "en": "Siyazan"},
    "sumgait": {"ru": "Сумгаит", "az": "Sumqayıt", "en": "Sumgait"},
    "tartar": {"ru": "Тертер", "az": "Tərtər", "en": "Tartar"},
    "tovuz": {"ru": "Товуз", "az": "Tovuz", "en": "Tovuz"},
    "ujar": {"ru": "Уджар", "az": "Ucar", "en": "Ujar"},
    "fizuli": {"ru": "Физули", "az": "Füzuli", "en": "Fizuli"},
    "khachmaz": {"ru": "Хачмаз", "az": "Xaçmaz", "en": "Khachmaz"},
    "khojavend": {"ru": "Ходжавенд", "az": "Xocavənd", "en": "Khojavend"},
    "khojaly": {"ru": "Ходжалы", "az": "Xocalı", "en": "Khojaly"},
    "khizi": {"ru": "Хызы", "az": "Xızı", "en": "Khizi"},
    "shabran": {"ru": "Шабран", "az": "Şabran", "en": "Shabran"},
    "shamakhi": {"ru": "Шамахы", "az": "Şamaxı", "en": "Shamakhi"},
    "shamkir": {"ru": "Шамкир", "az": "Şəmkir", "en": "Shamkir"},
    "sharur": {"ru": "Шарур", "az": "Şərur", "en": "Sharur"},
    "shahbuz": {"ru": "Шахбуз", "az": "Şahbuz", "en": "Shahbuz"},
    "sheki": {"ru": "Шеки", "az": "Şəki", "en": "Sheki"},
    "shirvan": {"ru": "Ширван", "az": "Şirvan", "en": "Shirvan"},
    "shusha": {"ru": "Шуша", "az": "Şuşa", "en": "Shusha"},
    "yardimly": {"ru": "Ярдымлы", "az": "Yardımlı", "en": "Yardimly"},
}

BAKU_DISTRICTS_MAP = {
    "baku_binagadi": {"ru": "Бинагадинский", "az": "Binəqədi", "en": "Binagadi"},
    "baku_garadagh": {"ru": "Гарадагский", "az": "Qaradağ", "en": "Garadagh"},
    "baku_khatai": {"ru": "Хатаинский", "az": "Xətai", "en": "Khatai"},
    "baku_khazar": {"ru": "Хазарский", "az": "Xəzər", "en": "Khazar"},
    "baku_narimanov": {"ru": "Наримановский", "az": "Nərimanov", "en": "Narimanov"},
    "baku_nasimi": {"ru": "Насиминский", "az": "Nəsimi", "en": "Nasimi"},
    "baku_nizami": {"ru": "Низаминский", "az": "Nizami", "en": "Nizami"},
    "baku_pirallahi": {"ru": "Пираллахинский", "az": "Pirallahı", "en": "Pirallahi"},
    "baku_sabail": {"ru": "Сабаильский", "az": "Səbail", "en": "Sabail"},
    "baku_sabunchu": {"ru": "Сабунчинский", "az": "Sabunçu", "en": "Sabunchu"},
    "baku_surakhani": {"ru": "Сураханский", "az": "Suraxanı", "en": "Surakhani"},
    "baku_yasamal": {"ru": "Ясамальский", "az": "Yasamal", "en": "Yasamal"},
}

LEGACY_MAPPING = {
    "баку": "baku",
    "baku": "baku",
    "bakı": "baku",
    "бинагади": "baku_binagadi",
    "binagadi": "baku_binagadi",
    "binəqədi": "baku_binagadi",
    "бинагадинский": "baku_binagadi",
    "гарадаг": "baku_garadagh",
    "garadagh": "baku_garadagh",
    "qaradağ": "baku_garadagh",
    "гарадагский": "baku_garadagh",
    "хатаи": "baku_khatai",
    "khatai": "baku_khatai",
    "xətai": "baku_khatai",
    "хатаинский": "baku_khatai",
    "хазар": "baku_khazar",
    "khazar": "baku_khazar",
    "xəzər": "baku_khazar",
    "хазарский": "baku_khazar",
    "нариманов": "baku_narimanov",
    "narimanov": "baku_narimanov",
    "nərimanov": "baku_narimanov",
    "наримановский": "baku_narimanov",
    "насими": "baku_nasimi",
    "nasimi": "baku_nasimi",
    "nəsimi": "baku_nasimi",
    "насиминский": "baku_nasimi",
    "низами": "baku_nizami",
    "nizami": "baku_nizami",
    "низаминский": "baku_nizami",
    "пираллахы": "baku_pirallahi",
    "pirallahi": "baku_pirallahi",
    "pirallahı": "baku_pirallahi",
    "пираллахинский": "baku_pirallahi",
    "сабаиль": "baku_sabail",
    "sabail": "baku_sabail",
    "səbail": "baku_sabail",
    "сабаильский": "baku_sabail",
    "сабунчи": "baku_sabunchu",
    "sabunchu": "baku_sabunchu",
    "sabunçu": "baku_sabunchu",
    "сабунчинский": "baku_sabunchu",
    "сураханы": "baku_surakhani",
    "surakhani": "baku_surakhani",
    "suraxanı": "baku_surakhani",
    "сураханский": "baku_surakhani",
    "ясамал": "baku_yasamal",
    "yasamal": "baku_yasamal",
    "ясамальский": "baku_yasamal",
}

def normalize_to_key(value: str) -> str:
    if not value:
        return ""
    val = str(value).strip().lower()
    if val in LEGACY_MAPPING:
        return LEGACY_MAPPING[val]
    # Check if there is a direct match in regions map by checking keys or values
    for k, info in AZERBAIJAN_REGIONS_MAP.items():
        if val == k or val in [v.lower() for v in info.values()]:
            return k
    for k, info in BAKU_DISTRICTS_MAP.items():
        if val == k or val in [v.lower() for v in info.values()]:
            return k
    return val

def migrate_to_hierarchy(apps, schema_editor):
    CatalogContentSettings = apps.get_model("catalog", "CatalogContentSettings")
    Place = apps.get_model("catalog", "Place")
    
    # 1. Update districts_json structure in settings
    baku_districts = []
    for k, trans in BAKU_DISTRICTS_MAP.items():
        baku_districts.append({
            "key": k,
            "name_ru": trans["ru"],
            "name_az": trans["az"],
            "name_en": trans["en"]
        })
    baku_districts.sort(key=lambda x: x["name_az"].casefold())
    
    new_hierarchy = [
        {
            "key": "baku",
            "name_ru": "Баку",
            "name_az": "Bakı",
            "name_en": "Baku",
            "districts": baku_districts
        }
    ]
    
    for k, trans in AZERBAIJAN_REGIONS_MAP.items():
        new_hierarchy.append({
            "key": k,
            "name_ru": trans["ru"],
            "name_az": trans["az"],
            "name_en": trans["en"]
        })
        
    settings_obj = CatalogContentSettings.objects.order_by("id").first()
    if settings_obj:
        settings_obj.districts_json = new_hierarchy
        settings_obj.save(update_fields=["districts_json", "updated_at"])
        
    # 2. Update Place district field values to stable keys
    for place in Place.objects.all().iterator():
        old_district = place.district
        if old_district:
            new_district = normalize_to_key(old_district)
            if new_district != old_district:
                place.district = new_district
                place.save(update_fields=["district"])

def rollback_hierarchy(apps, schema_editor):
    CatalogContentSettings = apps.get_model("catalog", "CatalogContentSettings")
    Place = apps.get_model("catalog", "Place")
    
    # Just restore the flat list of Russian names
    flat_list = ["Баку"]
    for k, trans in BAKU_DISTRICTS_MAP.items():
        flat_list.append(trans["ru"])
    for k, trans in AZERBAIJAN_REGIONS_MAP.items():
        flat_list.append(trans["ru"])
        
    settings_obj = CatalogContentSettings.objects.order_by("id").first()
    if settings_obj:
        settings_obj.districts_json = flat_list
        settings_obj.save(update_fields=["districts_json", "updated_at"])
        
    # Standard rollback for places is not strictly possible (loss of key mapping), but we can map back to Russian translations
    for place in Place.objects.all().iterator():
        old_district = place.district
        if old_district:
            if old_district in BAKU_DISTRICTS_MAP:
                place.district = BAKU_DISTRICTS_MAP[old_district]["ru"]
                place.save(update_fields=["district"])
            elif old_district in AZERBAIJAN_REGIONS_MAP:
                place.district = AZERBAIJAN_REGIONS_MAP[old_district]["ru"]
                place.save(update_fields=["district"])


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0049_mariadb_compatible_unique_constraints"),
    ]

    operations = [
        migrations.RunPython(migrate_to_hierarchy, rollback_hierarchy),
    ]
