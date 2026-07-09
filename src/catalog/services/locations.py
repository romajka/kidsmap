import re

from django.utils.translation import gettext as _

AZERBAIJAN_REGIONS_MAP = {
    "baku": {"ru": "Баку", "az": "Bakı", "en": "Baku"},
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

def get_location_translation(value: str, language_code: str = None) -> str:
    if not language_code:
        from django.utils import translation
        language_code = translation.get_language() or "az"
    key = normalize_to_key(value)
    lang = (language_code or "az").strip().split("-")[0].lower()
    if lang not in ("az", "ru", "en"):
        lang = "az"
        
    if key in BAKU_DISTRICTS_MAP:
        city_label = {"az": "Bakı", "ru": "Баку", "en": "Baku"}[lang]
        district_label = BAKU_DISTRICTS_MAP[key].get(lang, value)
        if lang == "az":
            return f"{city_label}, {district_label} rayonu"
        if lang == "en":
            return f"{district_label} District, {city_label}"
        return f"{city_label}, {district_label} район"
    if key in AZERBAIJAN_REGIONS_MAP:
        return AZERBAIJAN_REGIONS_MAP[key].get(lang, value)
    
    # Try translation lookup or return value as fallback
    from django.utils.translation import override
    with override(lang):
        return _(value)


def localize_address_text(value: str, language_code: str = None) -> str:
    if not value:
        return ""

    from django.conf import settings

    lang = ((language_code or settings.LANGUAGE_CODE or "az").split("-", 1)[0] or "az").lower()
    if lang not in ("az", "ru", "en"):
        lang = "az"
    if lang == "ru":
        return str(value).strip()

    localized = str(value).strip()

    proper_name_replacements = {
        "az": {
            "Школьная": "Məktəb",
            "Ататюрка": "Atatürk",
            "Гусейна Джавида": "Hüseyn Cavid",
        },
        "en": {
            "Школьная": "School",
            "Ататюрка": "Ataturk",
            "Гусейна Джавида": "Huseyn Javid",
        },
    }
    for source, target in proper_name_replacements.get(lang, {}).items():
        localized = localized.replace(source, target)

    replacements = {
        "az": [
            (r"\bАзербайджан\b", "Azərbaycan"),
            (r"\bБаку\b", "Bakı"),
            (r"\bгород\b", "şəhəri"),
            (r"\bрайон\b", "rayonu"),
            (r"\bул\.\s*", "küç. "),
            (r"\bулица\s+", ""),
            (r"\bпр\.\s*", "prospekti "),
            (r"\bпроспект\s+", ""),
            (r"\bпер\.\s*", "döngə "),
            (r"\bшоссе\b", "şossesi"),
        ],
        "en": [
            (r"\bАзербайджан\b", "Azerbaijan"),
            (r"\bБаку\b", "Baku"),
            (r"\bгород\b", "city"),
            (r"\bрайон\b", "district"),
            (r"\bул\.\s*", "St. "),
            (r"\bулица\s+", ""),
            (r"\bпр\.\s*", "Ave. "),
            (r"\bпроспект\s+", ""),
            (r"\bпер\.\s*", "Lane "),
            (r"\bшоссе\b", "Highway"),
        ],
    }
    for pattern, replacement in replacements[lang]:
        localized = re.sub(pattern, replacement, localized, flags=re.IGNORECASE)

    for key, labels in BAKU_DISTRICTS_MAP.items():
        variants = {
            key,
            labels["ru"],
            labels["az"],
            labels["en"],
            f"{labels['ru']} район",
            f"{labels['az']} rayonu",
            f"{labels['en']} District",
        }
        target = get_location_translation(key, lang)
        for variant in sorted(variants, key=len, reverse=True):
            localized = re.sub(re.escape(variant), target, localized, flags=re.IGNORECASE)

    for key, labels in AZERBAIJAN_REGIONS_MAP.items():
        variants = {key, labels["ru"], labels["az"], labels["en"]}
        target = get_location_translation(key, lang)
        for variant in sorted(variants, key=len, reverse=True):
            localized = re.sub(re.escape(variant), target, localized, flags=re.IGNORECASE)

    localized = re.sub(r"\s{2,}", " ", localized)
    localized = re.sub(r"\s+,", ",", localized)
    return localized.strip(" ,")

def get_regions_choices(language_code: str = "az") -> list[tuple[str, str]]:
    choices = []
    for key, trans in AZERBAIJAN_REGIONS_MAP.items():
        choices.append((key, trans.get(language_code) or trans.get("az") or key))
    # Sort by localized label, but Baku always first
    baku_choice = None
    other_choices = []
    for k, label in choices:
        if k == "baku":
            baku_choice = (k, label)
        else:
            other_choices.append((k, label))
    other_choices.sort(key=lambda x: x[1].casefold())
    
    result = []
    if baku_choice:
        result.append(baku_choice)
    result.extend(other_choices)
    return result

def get_baku_districts_choices(language_code: str = "az") -> list[tuple[str, str]]:
    choices = []
    for key, trans in BAKU_DISTRICTS_MAP.items():
        choices.append((key, trans.get(language_code) or trans.get("az") or key))
    choices.sort(key=lambda x: x[1].casefold())
    return choices

def get_all_districts_flat_choices(language_code: str = "az") -> list[tuple[str, str]]:
    choices = []
    for key, trans in AZERBAIJAN_REGIONS_MAP.items():
        choices.append((key, trans.get(language_code) or trans.get("az") or key))
    for key, trans in BAKU_DISTRICTS_MAP.items():
        choices.append((key, trans.get(language_code) or trans.get("az") or key))
    return choices


def init_location_fields(form, instance):
    db_district = (form.initial.get("district") or (instance and getattr(instance, "district", "")) or "").strip()
    if db_district.startswith("baku_"):
        initial_region = "baku"
        initial_district = db_district
    elif db_district == "baku":
        initial_region = "baku"
        initial_district = ""
    elif db_district:
        initial_region = db_district
        initial_district = ""
    else:
        initial_region = ""
        initial_district = ""

    form.initial["region"] = initial_region
    form.initial["district"] = initial_district


def configure_location_choices(form):
    from catalog.services.locations import get_regions_choices, get_baku_districts_choices
    from django.utils.translation import get_language
    lang = get_language() or "az"

    regions = get_regions_choices(lang)
    districts = get_baku_districts_choices(lang)

    form.fields["region"].choices = [("", _("Выберите регион"))] + regions
    form.fields["district"].choices = [("", _("Выберите район"))] + districts

    form.fields["region"].help_text = _("Выберите город или регион.")
    form.fields["district"].help_text = _("Выберите район Баку.")
    form.fields["region"].error_messages.update({"invalid_choice": _("Выберите регион из списка.")})
    form.fields["district"].error_messages.update({"invalid_choice": _("Выберите район из списка.")})


def clean_location_fields(form, cleaned):
    region = (cleaned.get("region") or "").strip()
    district = (cleaned.get("district") or "").strip()

    # Security: reject cross-region POST manipulation.
    # Example: region=ganja + district=baku_yasamal must never reach the DB.
    if district.startswith("baku_") and region != "baku":
        form.add_error(
            "district",
            _("Район Баку нельзя выбрать для другого региона."),
        )
        district = ""

    # Reject a non-Baku region key submitted in the district field while region=baku.
    if region == "baku" and district and not district.startswith("baku_") and district in AZERBAIJAN_REGIONS_MAP:
        form.add_error(
            "district",
            _("Для Баку выберите один из районов Баку."),
        )
        district = ""

    if not getattr(form, "draft_save_only", False) and getattr(form, "require_location_region", True):
        if not region:
            form.add_error("region", _("Выберите регион или город."))
        elif region == "baku":
            if not district:
                form.add_error("district", _("Для Баку необходимо выбрать район."))

    if region == "baku":
        cleaned["district"] = district or ""
    else:
        # For non-Baku regions, the district column stores the region key itself.
        cleaned["district"] = region or ""
    return cleaned
