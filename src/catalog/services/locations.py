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
    "khankendi": {"ru": "Ханкенди", "az": "Xankəndi", "en": "Khankendi"},
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
    "шамахы": "shamakhi",
    "шамаха": "shamakhi",
    "шемаха": "shamakhi",
    "шамахи": "shamakhi",
    "shamakhi": "shamakhi",
    "şamaxı": "shamakhi",
    "ханкенди": "khankendi",
    "khankendi": "khankendi",
    "xankəndi": "khankendi",
    "степанакерт": "khankendi",
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

BAKU_METRO_MAP = {
    "28_may": {"ru": "28 Мая", "az": "28 May", "en": "28 May"},
    "genclik": {"ru": "Гянджлик", "az": "Gənclik", "en": "Genclik"},
    "narimanov": {"ru": "Нариман Нариманов", "az": "Nəriman Nərimanov", "en": "Nariman Narimanov"},
    "elmler": {"ru": "Эльмляр Академиясы", "az": "Elmlər Akademiyası", "en": "Elmler Akademiyasi"},
    "icherisheher": {"ru": "Ичеришехер", "az": "İçərişəhər", "en": "Icherisheher"},
    "20_yanvar": {"ru": "20 Января", "az": "20 Yanvar", "en": "20 January"},
    "memar_ecemi": {"ru": "Мемар Аджеми", "az": "Memar Əcəmi", "en": "Memar Ajami"},
    "inshaatchilar": {"ru": "Иншаатчылар", "az": "İnşaatçılar", "en": "Inshaatchilar"},
    "khatai": {"ru": "Хатаи", "az": "Xətai", "en": "Khatai"},
    "sahil": {"ru": "Сахил", "az": "Sahil", "en": "Sahil"},
    "koroglu": {"ru": "Кёроглу", "az": "Koroğlu", "en": "Koroglu"},
    "azadlig": {"ru": "Азадлыг проспекти", "az": "Azadlıq prospekti", "en": "Azadlig avenue"},
    "nasimi": {"ru": "Насими", "az": "Nəsimi", "en": "Nasimi"},
    "ag_sheher": {"ru": "Белый город", "az": "Ağ Şəhər", "en": "White City"},
    "nizami": {"ru": "Низами", "az": "Nizami", "en": "Nizami"},
    "qara_qarayev": {"ru": "Кара Караев", "az": "Qara Qarayev", "en": "Gara Garayev"},
    "neftchilar": {"ru": "Нефтчиляр", "az": "Neftçilər", "en": "Neftchilar"},
    "xalqlar": {"ru": "Халглар Достлугу", "az": "Xalqlar Dostluğu", "en": "Khalglar Dostlugu"},
    "ehmedli": {"ru": "Ахмедлы", "az": "Əhmədli", "en": "Ahmedli"},
    "hezi_aslanov": {"ru": "Ази Асланов", "az": "Həzi Aslanov", "en": "Hazi Aslanov"},
    "ulduz": {"ru": "Улдуз", "az": "Ulduz", "en": "Ulduz"},
    "bakmil": {"ru": "Бакмил", "az": "Bakmil", "en": "Bakmil"},
    "dernegul": {"ru": "Дарнагюль", "az": "Dərnəgül", "en": "Dernegul"},
    "avtovagzal": {"ru": "Автовокзал", "az": "Avtovağzal", "en": "Avtovagzal"},
    "8_noyabr": {"ru": "8 Ноября", "az": "8 Noyabr", "en": "8 November"},
    "xocasen": {"ru": "Ходжасан", "az": "Xocəsən", "en": "Khojasan"},
}

METRO_LEGACY_MAPPING = {
    "28 мая": "28_may",
    "28 may": "28_may",
    "гянджлик": "genclik",
    "gənclik": "genclik",
    "genclik": "genclik",
    "нариман нариманов": "narimanov",
    "нариманов": "narimanov",
    "nəriman nərimanov": "narimanov",
    "nərimanov": "narimanov",
    "narimanov": "narimanov",
    "nariman narimanov": "narimanov",
    "эльмляр академиясы": "elmler",
    "эльмляр": "elmler",
    "академия наук": "elmler",
    "elmlər akademiyası": "elmler",
    "elmlər": "elmler",
    "elmler akademiyasi": "elmler",
    "ичеришехер": "icherisheher",
    "ичери шехер": "icherisheher",
    "içərişəhər": "icherisheher",
    "içəri şəhər": "icherisheher",
    "icherisheher": "icherisheher",
    "20 января": "20_yanvar",
    "20 yanvar": "20_yanvar",
    "мемар аджеми": "memar_ecemi",
    "memar əcəmi": "memar_ecemi",
    "memar ecemi": "memar_ecemi",
    "memar ajami": "memar_ecemi",
    "иншаатчылар": "inshaatchilar",
    "i̇nşaatçılar": "inshaatchilar",
    "inşaatçılar": "inshaatchilar",
    "inshaatchilar": "inshaatchilar",
    "хатаи": "khatai",
    "xətai": "khatai",
    "khatai": "khatai",
    "сахил": "sahil",
    "sahil": "sahil",
    "кёроглу": "koroglu",
    "короглу": "koroglu",
    "koroğlu": "koroglu",
    "koroglu": "koroglu",
    "азадлыг": "azadlig",
    "азадлыг проспекти": "azadlig",
    "azadlıq": "azadlig",
    "azadlıq prospekti": "azadlig",
    "насими": "nasimi",
    "nəsimi": "nasimi",
    "nasimi": "nasimi",
    "белый город": "ag_sheher",
    "аг шехер": "ag_sheher",
    "ağ şəhər": "ag_sheher",
    "ag sheher": "ag_sheher",
    "низами": "nizami",
    "nizami": "nizami",
    "кара караев": "qara_qarayev",
    "qara qarayev": "qara_qarayev",
    "нефтчиляр": "neftchilar",
    "neftçilər": "neftchilar",
    "халглар достлугу": "xalqlar",
    "xalqlar dostluğu": "xalqlar",
    "ахмедлы": "ehmedli",
    "əhmədli": "ehmedli",
    "ази асланов": "hezi_aslanov",
    "həzi aslanov": "hezi_aslanov",
    "улдуз": "ulduz",
    "ulduz": "ulduz",
    "бакмил": "bakmil",
    "bakmil": "bakmil",
    "дарнагюль": "dernegul",
    "dərnəgül": "dernegul",
    "автовокзал": "avtovagzal",
    "avtovağzal": "avtovagzal",
    "8 ноября": "8_noyabr",
    "8 noyabr": "8_noyabr",
    "ходжасан": "xocasen",
    "xocəsən": "xocasen",
}

def get_metro_translation(value: str, language_code: str = None) -> str:
    if not value:
        return ""
    if not language_code:
        from django.utils import translation
        language_code = translation.get_language() or "az"
    lang = (language_code or "az").strip().split("-")[0].lower()
    if lang not in ("az", "ru", "en"):
        lang = "az"

    val = str(value).strip().lower()
    key = METRO_LEGACY_MAPPING.get(val)
    if not key:
        for k, info in BAKU_METRO_MAP.items():
            if val == k or val in [v.lower() for v in info.values()]:
                key = k
                break
    if key and key in BAKU_METRO_MAP:
        return BAKU_METRO_MAP[key].get(lang, value)

    from django.utils.translation import override
    with override(lang):
        return _(value)

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


_LOCATION_SUFFIXES = {
    "city": ("şəhəri", "city", "город"),
    "district": ("rayonu", "district", "район"),
}

_LOCALIZED_SUFFIXES = {
    "az": {"city": "şəhəri", "district": "rayonu"},
    "en": {"city": "city", "district": "District"},
    "ru": {"city": "город", "district": "район"},
}


def _normalize_location_segment(segment: str, lang: str) -> tuple[str, str]:
    normalized_segment = re.sub(r"\s+", " ", segment).strip()
    suffix_type = ""
    base = normalized_segment

    for candidate_type, suffixes in _LOCATION_SUFFIXES.items():
        suffix_pattern = "|".join(re.escape(suffix) for suffix in suffixes)
        match = re.fullmatch(
            rf"(?P<base>.*?)(?:\s+(?:{suffix_pattern}))+",
            normalized_segment,
            flags=re.IGNORECASE,
        )
        if match:
            base = match.group("base").strip()
            suffix_type = candidate_type
            break

    key = normalize_to_key(base)
    if key in BAKU_DISTRICTS_MAP:
        identity = f"district:{key}"
    elif key in AZERBAIJAN_REGIONS_MAP:
        identity = f"region:{key}"
    else:
        identity = ""

    if suffix_type:
        if key in BAKU_DISTRICTS_MAP:
            base = BAKU_DISTRICTS_MAP[key][lang]
        elif key in AZERBAIJAN_REGIONS_MAP:
            base = AZERBAIJAN_REGIONS_MAP[key][lang]
        normalized_segment = f"{base} {_LOCALIZED_SUFFIXES[lang][suffix_type]}"

    return normalized_segment, identity


def _deduplicate_location_segments(value: str, lang: str) -> str:
    segments = []
    seen_locations = set()

    for raw_segment in value.split(","):
        segment = raw_segment.strip()
        if not segment:
            continue

        normalized_segment, identity = _normalize_location_segment(segment, lang)
        if identity and identity in seen_locations:
            continue
        if identity:
            seen_locations.add(identity)
        segments.append(normalized_segment)

    return ", ".join(segments).strip(" ,")


def localize_address_text(value: str, language_code: str = None) -> str:
    if not value:
        return ""

    from django.conf import settings

    lang = ((language_code or settings.LANGUAGE_CODE or "az").split("-", 1)[0] or "az").lower()
    if lang not in ("az", "ru", "en"):
        lang = "az"
    if lang == "ru":
        return _deduplicate_location_segments(str(value).strip(), lang)

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

    for key, labels in BAKU_DISTRICTS_MAP.items():
        variants = {
            key,
            labels["ru"],
            labels["az"],
            labels["en"],
            f"{labels['ru']} район",
            f"{labels['ru']} rayonu",
            f"{labels['az']} rayonu",
            f"{labels['en']} District",
        }
        target = get_location_translation(key, lang)
        for variant in sorted(variants, key=len, reverse=True):
            localized = re.sub(re.escape(variant), target, localized, flags=re.IGNORECASE)

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

    for key, labels in AZERBAIJAN_REGIONS_MAP.items():
        variants = {key, labels["ru"], labels["az"], labels["en"]}
        target = get_location_translation(key, lang)
        for variant in sorted(variants, key=len, reverse=True):
            localized = re.sub(re.escape(variant), target, localized, flags=re.IGNORECASE)

    return _deduplicate_location_segments(localized, lang)

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
    lang = (get_language() or "az").split("-")[0]

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
