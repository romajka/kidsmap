"""Specialist directory, specialist pages and owner specialist editing."""

from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST
from ..forms import OwnerSpecialistForm
from ..models import Specialist
from ..services.owner_specialist_use_cases import save_owner_specialist_profile
from ..services.features import require_specialists_section_enabled
from .common import _engagement_login_required_response, _redirect_to_login
from .public import _review_submission_response


def serve_specialist_document(request, document_id):
    require_specialists_section_enabled()
    from catalog.models import SpecialistDocument
    from django.http import FileResponse, Http404

    doc = get_object_or_404(SpecialistDocument, pk=document_id)
    from catalog.services.specialist_documents import can_download_document
    if not can_download_document(request.user, doc):
        raise Http404(_("Документ не найден или доступ ограничен."))
    # Legacy public files require an explicitly verified operational transition.
    if not doc.file or not doc.file.name.startswith('specialist-documents/'):
        raise Http404()
    try:
        response = FileResponse(doc.file.open('rb'), as_attachment=True, filename='document.bin',
                                content_type='application/octet-stream')
    except (OSError, ValueError):
        raise Http404() from None
    response['Cache-Control'] = 'private, no-store'
    response['X-Content-Type-Options'] = 'nosniff'
    response['Content-Security-Policy'] = "sandbox; default-src 'none'"
    return response

def specialist_list(request):
    require_specialists_section_enabled()

    from catalog.models import Specialist, SpecialistSpecialization, Region, District, MetroStation, SpecialistPracticeLocation
    from catalog.services.public_filter_options import build_public_specialist_filter_options
    from catalog.services.specialist_filtering import (
        apply_specialist_price_filter, get_specialist_max_price,
        normalize_specialist_price_bounds,
    )
    from django.db import models
    from django.core.paginator import Paginator

    from django.db.models import Prefetch
    qs = Specialist.objects.filter(status=Specialist.STATUS_PUBLISHED, is_active=True).prefetch_related(
        Prefetch('practice_locations', queryset=SpecialistPracticeLocation.objects.filter(is_active=True)
                 .select_related('place', 'region', 'district', 'metro')), 'specializations')

    from catalog.services.specialist_subjects import SUBJECTS, TUTOR_CODES, subject_item, profile_subjects

    # 1. Search Query
    q = (request.GET.get("q") or "").strip()
    if q:
        subject_matches = [code for code, labels in SUBJECTS.items()
                           if any(q.casefold() in label.casefold() for label in labels[:3])]
        qs = qs.filter(
            models.Q(name__icontains=q)
            | models.Q(name_alt__icontains=q)
            | models.Q(bio_ru__icontains=q)
            | models.Q(bio_az__icontains=q)
            | models.Q(bio_en__icontains=q)
            | models.Q(specializations__name__icontains=q)
            | models.Q(specializations__name_ru__icontains=q)
            | models.Q(specializations__name_az__icontains=q)
            | models.Q(specializations__name_en__icontains=q)
            | models.Q(specializations__code__in=subject_matches)
        )

    # 2. Specialization
    spec_code = (request.GET.get("specialization") or "").strip()
    if spec_code == 'tutor':
        qs = qs.filter(specializations__code__in=TUTOR_CODES)
    elif spec_code:
        qs = qs.filter(specializations__code=spec_code)
    subject_code = (request.GET.get('subject') or '').strip()
    if subject_code:
        qs = qs.filter(specializations__code=subject_code) if subject_code in SUBJECTS else qs.none()

    # 3. Consultation Format
    cf = (request.GET.get("format") or "").strip()
    if cf:
        if cf == "online":
            qs = qs.filter(consultation_format__in=[Specialist.FORMAT_ONLINE, Specialist.FORMAT_BOTH])
        elif cf == "offline":
            qs = qs.filter(consultation_format__in=[Specialist.FORMAT_OFFLINE, Specialist.FORMAT_BOTH])

    # 4. Location Filters
    region_key = (request.GET.get("region") or "").strip()
    district_key = (request.GET.get("district") or "").strip()
    metro_key = (request.GET.get("metro") or "").strip()

    if region_key or district_key or metro_key:
        loc_q = models.Q(practice_locations__is_active=True)
        if region_key:
            loc_q &= models.Q(practice_locations__region_id=region_key)
        if district_key:
            loc_q &= models.Q(practice_locations__district_id=district_key)
        if metro_key:
            loc_q &= models.Q(practice_locations__metro_id=metro_key)
        qs = qs.filter(loc_q)

    # 5. Age (supports age_from and age_to range like catalog places, with fallback to single age)
    age = (request.GET.get("age") or "").strip()
    age_from = (request.GET.get("age_from") or "").strip()
    age_to = (request.GET.get("age_to") or "").strip()

    if age_from.isdigit() or age_to.isdigit():
        af_val = int(age_from) if age_from.isdigit() else 0
        at_val = int(age_to) if age_to.isdigit() else 18
        if not (af_val == 0 and at_val == 18):
            qs = qs.filter(
                (models.Q(age_from__isnull=True) | models.Q(age_from__lte=at_val))
                & (models.Q(age_to__isnull=True) | models.Q(age_to__gte=af_val))
            )
    elif age.isdigit():
        age_val = int(age)
        qs = qs.filter(
            (models.Q(age_from__isnull=True) | models.Q(age_from__lte=age_val))
            & (models.Q(age_to__isnull=True) | models.Q(age_to__gte=age_val))
        )

    # 6. One global ceiling and semantic bounds for SQL, chips and forms.
    specialist_price_max = get_specialist_max_price()
    price_lower, price_upper = normalize_specialist_price_bounds(
        request.GET.get("price_from"), request.GET.get("price_to"),
        ceiling=specialist_price_max,
    )
    price_from = str(price_lower) if price_lower is not None else ""
    price_to = str(price_upper) if price_upper is not None else ""
    qs = apply_specialist_price_filter(qs, price_lower, price_upper)

    # 6a. Consultation Language
    consult_lang = (request.GET.get("language") or "").strip()
    if consult_lang in ["az", "ru", "en"]:
        qs = qs.filter(**{f"language_{consult_lang}": True})

    # 6b. Verified Specialist

    # 6c. Minimum Rating
    min_rating = (request.GET.get("min_rating") or "").strip()
    if min_rating:
        try:
            qs = qs.filter(rating_avg__gte=float(min_rating))
        except ValueError:
            pass

    # 7. Sorting
    sort = (request.GET.get("sort") or "new").strip()
    if sort == "rating":
        qs = qs.order_by("-rating_avg", "-rating_count", "-created_at")
    elif sort == "price_asc":
        from django.db.models.functions import Coalesce
        from django.db.models import Min
        qs = qs.annotate(
            min_price=Coalesce(Min("practice_locations__price_per_session", filter=models.Q(practice_locations__is_active=True)), "price_from")
        ).order_by("min_price", "-created_at")
    elif sort == "price_desc":
        from django.db.models.functions import Coalesce
        from django.db.models import Max
        qs = qs.annotate(
            max_price=Coalesce(Max("practice_locations__price_per_session", filter=models.Q(practice_locations__is_active=True)), "price_to")
        ).order_by("-max_price", "-created_at")
    elif sort == "experience":
        qs = qs.order_by("-experience_years", "-created_at")
    else:
        qs = qs.order_by("-created_at")

    qs = qs.distinct()

    paginator = Paginator(qs, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    active_filter_chips = []
    language = (request.LANGUAGE_CODE or "az").split("-")[0]

    specialist_query_params = request.GET.copy()
    specialist_query_params.pop("page", None)
    for name, value in (("price_from", price_from), ("price_to", price_to)):
        specialist_query_params.pop(name, None)
        if value:
            specialist_query_params[name] = value

    def rebuild_url(*exclude_params):
        params = specialist_query_params.copy()
        for name in exclude_params:
            params.pop(name, None)
        return f"?{params.urlencode()}" if params else request.path

    if q:
        active_filter_chips.append({
            "label": f"{_('Поиск')}: {q}",
            "remove_url": rebuild_url("q")
        })
    if spec_code:
        spec_obj = SpecialistSpecialization.objects.filter(code=spec_code).first()
        if spec_obj:
            active_filter_chips.append({
                "label": spec_obj.name_i18n(language),
                "remove_url": rebuild_url("specialization")
            })
    if subject_code:
        active_filter_chips.append({
            'label': subject_item(subject_code, language)['label'] if subject_code in SUBJECTS else subject_code,
            'remove_url': rebuild_url('subject'),
        })
    if cf:
        format_labels = {
            "online": _("Онлайн"),
            "offline": _("Очно"),
        }
        active_filter_chips.append({
            "label": format_labels.get(cf, cf),
            "remove_url": rebuild_url("format")
        })
    if region_key:
        reg_obj = Region.objects.filter(key=region_key).first()
        if reg_obj:
            active_filter_chips.append({
                "label": reg_obj.name_i18n(language),
                "remove_url": rebuild_url("region")
            })
    if district_key:
        dist_obj = District.objects.filter(key=district_key).first()
        if dist_obj:
            active_filter_chips.append({
                "label": dist_obj.name_i18n(language),
                "remove_url": rebuild_url("district")
            })
    if metro_key:
        metro_obj = MetroStation.objects.filter(key=metro_key).first()
        if metro_obj:
            active_filter_chips.append({
                "label": metro_obj.name_i18n(language),
                "remove_url": rebuild_url("metro")
            })
    if (age_from or age_to) and not (age_from in {"", "0"} and age_to in {"", "18"}):
        if language == "az":
            age_label = f"{age_from or '0'}–{age_to or '18'} yaş"
        elif language == "en":
            age_label = f"{age_from or '0'}–{age_to or '18'} years"
        else:
            age_label = f"{age_from or '0'}–{age_to or '18'} лет"
        active_filter_chips.append({
            "label": f"{_('Возраст')}: {age_label}",
            "remove_url": rebuild_url("age_from", "age_to", "age")
        })
    elif age:
        active_filter_chips.append({
            "label": f"{_('Возраст')}: {age}",
            "remove_url": rebuild_url("age")
        })
    if price_from or price_to:
        if price_to:
            price_label = f"{price_from or '0'}–{price_to} ₼"
        elif language == "az":
            price_label = f"{price_from} ₼-dən"
        elif language == "en":
            price_label = f"from {price_from} ₼"
        else:
            price_label = f"от {price_from} ₼"
        active_filter_chips.append({
            "label": price_label,
            "remove_url": rebuild_url("price_from", "price_to")
        })
    if consult_lang:
        lang_labels = {
            "az": _("Азербайджанский"),
            "ru": _("Русский"),
            "en": _("Английский"),
        }
        active_filter_chips.append({
            "label": f"{_('Язык')}: {lang_labels.get(consult_lang, consult_lang)}",
            "remove_url": rebuild_url("language")
        })
    if min_rating:
        active_filter_chips.append({
            "label": f"{_('Рейтинг')} ≥ {min_rating}",
            "remove_url": rebuild_url("min_rating")
        })

    filter_options = build_public_specialist_filter_options(language_code=language)

    subject_options = [dict(subject_item(s['value'], language), count=s['count'])
                       for s in filter_options.specializations if s['value'] in SUBJECTS]
    subject_options.sort(key=lambda item: list(SUBJECTS).index(item['value']))
    for item in subject_options:
        params = specialist_query_params.copy()
        params['specialization'] = 'tutor'
        params['subject'] = item['value']
        item['url'] = '?' + params.urlencode()
    filter_options.specializations[:] = [s for s in filter_options.specializations
                                         if s['value'] not in SUBJECTS or s['value'] == spec_code]
    filter_options.specializations.sort(key=lambda item: item['value'] != 'tutor')

    SPECIALIST_VISUALS = {
        "speech_therapist": {"icon": "record_voice_over", "color_bg": "#ede9fe", "color_text": "#7c3aed"},
        "psychologist": {"icon": "psychology", "color_bg": "#e0f2fe", "color_text": "#0284c7"},
        "child_psychologist": {"icon": "psychology_alt", "color_bg": "#e0f2fe", "color_text": "#0284c7"},
        "sports_psychologist": {"icon": "sports_score", "color_bg": "#e0f2fe", "color_text": "#0284c7"},
        "sports_coach": {"icon": "sports_soccer", "color_bg": "#ccfbf1", "color_text": "#0f766e"},
        "personal_trainer": {"icon": "fitness_center", "color_bg": "#ccfbf1", "color_text": "#0f766e"},
        "posture_correction_specialist": {"icon": "accessibility_new", "color_bg": "#ccfbf1", "color_text": "#0f766e"},
        "physical_rehab_specialist": {"icon": "assist_walker", "color_bg": "#ccfbf1", "color_text": "#0f766e"},
        "tutor": {"icon": "school", "color_bg": "#fef3c7", "color_text": "#b45309"},
        "primary_teacher": {"icon": "history_edu", "color_bg": "#fef3c7", "color_text": "#b45309"},
        "school_prep_teacher": {"icon": "draw", "color_bg": "#fef3c7", "color_text": "#b45309"},
        "math_tutor": {"icon": "calculate", "color_bg": "#fef3c7", "color_text": "#b45309"},
        "exam_prep_tutor": {"icon": "assignment", "color_bg": "#fef3c7", "color_text": "#b45309"},
        "english_teacher": {"icon": "translate", "color_bg": "#fef3c7", "color_text": "#b45309"},
        "russian_teacher": {"icon": "translate", "color_bg": "#fef3c7", "color_text": "#b45309"},
        "azerbaijani_teacher": {"icon": "translate", "color_bg": "#fef3c7", "color_text": "#b45309"},
        "pathologist": {"icon": "extension", "color_bg": "#fae8ff", "color_text": "#a21caf"},
        "early_development_specialist": {"icon": "child_care", "color_bg": "#ffe4e6", "color_text": "#be123c"},
        "sensory_integration": {"icon": "fingerprint", "color_bg": "#fae8ff", "color_text": "#a21caf"},
        "neuropediatrician": {"icon": "neurology", "color_bg": "#e0f7fa", "color_text": "#00838f"},
        "pediatrician": {"icon": "medical_services", "color_bg": "#e0f7fa", "color_text": "#00838f"},
        "physiotherapist": {"icon": "health_and_safety", "color_bg": "#e0f7fa", "color_text": "#00838f"},
        "rehab_specialist": {"icon": "healing", "color_bg": "#e0f7fa", "color_text": "#00838f"},
        "music_teacher": {"icon": "music_note", "color_bg": "#fce7f3", "color_text": "#be185d"},
        "drawing_teacher": {"icon": "palette", "color_bg": "#fed7aa", "color_text": "#c2410c"},
        "acting_teacher": {"icon": "theater_comedy", "color_bg": "#fed7aa", "color_text": "#c2410c"},
        "programming_mentor": {"icon": "code", "color_bg": "#dbeafe", "color_text": "#1d4ed8"},
        "robotics_teacher": {"icon": "smart_toy", "color_bg": "#dbeafe", "color_text": "#1d4ed8"},
        "career_guidance_specialist": {"icon": "explore", "color_bg": "#e2e8f0", "color_text": "#475569"},
    }

    specialization_chips = []
    for spec in filter_options.specializations:
        val = spec["value"]
        visual = SPECIALIST_VISUALS.get(val, {"icon": "school", "color_bg": "#f1f5f9", "color_text": "#475569"})
        chip_params = specialist_query_params.copy()
        chip_params["specialization"] = val
        if val not in ("tutor", "exam_prep_tutor"):
            chip_params.pop("subject", None)
        chip_url = f"?{chip_params.urlencode()}"
        specialization_chips.append({
            "value": val,
            "label": spec["label"],
            "count": spec.get("count", 0),
            "url": chip_url,
            "icon": visual["icon"],
            "color_bg": visual["color_bg"],
            "color_text": visual["color_text"],
            "is_active": (spec_code == val),
        })

    specialization_chips.sort(
        key=lambda c: (0 if c["value"] == "tutor" else 1, 0 if (c["count"] > 0 or c["is_active"]) else 1, -c["count"])
    )
    all_params = specialist_query_params.copy()
    all_params.pop('specialization', None)
    all_params.pop('subject', None)
    all_specializations_url = '?' + all_params.urlencode() if all_params else '?'
    tutor_params = all_params.copy()
    tutor_params['specialization'] = 'tutor'
    all_tutors_url = '?' + tutor_params.urlencode()

    # Count specialists matching the current filters
    count = qs.count()
    if language == "az":
        results_count_label = f"{count} mütəxəssis tapıldı"
    elif language == "en":
        results_count_label = f"Found {count} specialist" if count == 1 else f"Found {count} specialists"
    else:
        rem10 = count % 10
        rem100 = count % 100
        if rem10 == 1 and rem100 != 11:
            results_count_label = f"Найден {count} специалист"
        elif 2 <= rem10 <= 4 and not (12 <= rem100 <= 14):
            results_count_label = f"Найдено {count} специалиста"
        else:
            results_count_label = f"Найдено {count} специалистов"

    # Enrich specialist cards with strictly ordered and preformatted metadata
    for specialist in page_obj:
        # Check if photo exists on storage
        specialist.has_valid_photo = False
        if specialist.photo:
            try:
                if specialist.photo.storage.exists(specialist.photo.name):
                    specialist.has_valid_photo = True
            except Exception:
                specialist.has_valid_photo = False

        # 0. Initials for avatar placeholder
        name_parts = (specialist.name or "").strip().split()
        if len(name_parts) >= 2:
            specialist.card_initials = (name_parts[0][:1] + name_parts[1][:1]).upper()
        elif len(name_parts) == 1:
            specialist.card_initials = name_parts[0][:2].upper()
        else:
            specialist.card_initials = "KM"

        # 1. Specialization list
        specialist.card_subjects = profile_subjects(specialist, language)
        specialist.card_specializations = [s.name_i18n(language) for s in specialist.specializations.all() if s.code not in SUBJECTS]

        # 2. Age range
        if specialist.age_from and specialist.age_to:
            if language == "az":
                specialist.card_age = f"{specialist.age_from}–{specialist.age_to} yaş"
            elif language == "en":
                specialist.card_age = f"{specialist.age_from}–{specialist.age_to} yrs"
            else:
                specialist.card_age = f"{specialist.age_from}–{specialist.age_to} лет"
        elif specialist.age_from:
            if language == "az":
                specialist.card_age = f"{specialist.age_from} yaşdan"
            elif language == "en":
                specialist.card_age = f"From {specialist.age_from} yrs"
            else:
                specialist.card_age = f"С {specialist.age_from} лет"
        elif specialist.age_to:
            if language == "az":
                specialist.card_age = f"{specialist.age_to} yaşadək"
            elif language == "en":
                specialist.card_age = f"Up to {specialist.age_to} yrs"
            else:
                specialist.card_age = f"До {specialist.age_to} лет"
        else:
            if language == "az":
                specialist.card_age = "İstənilən yaş"
            elif language == "en":
                specialist.card_age = "Any age"
            else:
                specialist.card_age = "Любой возраст"

        # 3. Format
        fmt = specialist.consultation_format
        if fmt == Specialist.FORMAT_ONLINE:
            specialist.card_format_label = "Onlayn" if language == "az" else ("Online" if language == "en" else "Онлайн")
            specialist.card_format_icon = "videocam"
        elif fmt == Specialist.FORMAT_OFFLINE:
            specialist.card_format_label = "Otaqda (Əyani)" if language == "az" else ("In Office" if language == "en" else "Очно (в кабинете)")
            specialist.card_format_icon = "location_on"
        else:
            specialist.card_format_label = "Onlayn və əyani" if language == "az" else ("Online & In Office" if language == "en" else "Онлайн и очно")
            specialist.card_format_icon = "devices"

        # 4. District / Location
        if fmt == Specialist.FORMAT_ONLINE:
            specialist.card_location = "Bütün Azərbaycan üzrə onlayn" if language == "az" else ("Online across Azerbaijan" if language == "en" else "Онлайн по всему Азербайджану")
        else:
            loc_names = []
            for loc in specialist.practice_locations.all():
                loc_label = None
                if loc.district:
                    loc_label = loc.district.name_i18n(language)
                elif loc.metro:
                    loc_label = loc.metro.name_i18n(language)
                elif loc.place and loc.place.district:
                    loc_label = loc.place.district_i18n(language)
                elif loc.address:
                    loc_label = loc.address
                if loc_label and loc_label not in loc_names:
                    loc_names.append(loc_label)
            if loc_names:
                specialist.card_location = ", ".join(loc_names)
            elif fmt in [Specialist.FORMAT_ONLINE, Specialist.FORMAT_BOTH]:
                specialist.card_location = "Bütün Azərbaycan üzrə onlayn" if language == "az" else ("Online across Azerbaijan" if language == "en" else "Онлайн по всему Азербайджану")
            else:
                specialist.card_location = "Bakı" if language == "az" else ("Baku" if language == "en" else "Баку")

        # 5. Price
        session_suffix = " / seans" if language == "az" else (" / session" if language == "en" else " / приём")
        if specialist.price_from and specialist.price_to:
            specialist.card_price = f"{specialist.price_from}–{specialist.price_to} AZN{session_suffix}"
        elif specialist.price_from:
            if language == "az":
                specialist.card_price = f"{specialist.price_from} AZN-dən{session_suffix}"
            elif language == "en":
                specialist.card_price = f"from {specialist.price_from} AZN{session_suffix}"
            else:
                specialist.card_price = f"от {specialist.price_from} AZN{session_suffix}"
        elif specialist.price_to:
            if language == "az":
                specialist.card_price = f"{specialist.price_to} AZN-dək{session_suffix}"
            elif language == "en":
                specialist.card_price = f"up to {specialist.price_to} AZN{session_suffix}"
            else:
                specialist.card_price = f"до {specialist.price_to} AZN{session_suffix}"
        else:
            locs = list(specialist.practice_locations.all())
            is_free = any(l.price_per_session == 0 for l in locs)
            prices = [l.price_per_session for l in locs if l.price_per_session and l.price_per_session > 0]
            if is_free and not prices:
                specialist.card_price = "Pulsuz" if language == "az" else ("Free" if language == "en" else "Бесплатно")
            elif prices:
                min_p = min(prices)
                max_p = max(prices)
                if min_p == max_p:
                    specialist.card_price = f"{min_p} AZN{session_suffix}"
                else:
                    specialist.card_price = f"{min_p}–{max_p} AZN{session_suffix}"
            else:
                specialist.card_price = "Razılaşma yolu ilə" if language == "az" else ("By agreement" if language == "en" else "По договорённости")

    context = {
        "subject_options": subject_options,
        "specialist_price_max": specialist_price_max,
        "page_obj": page_obj,
        "specialists": page_obj,
        "selected": {
            "q": q,
            "specialization": spec_code,
            "subject": subject_code,
            "format": cf,
            "region": region_key,
            "district": district_key,
            "metro": metro_key,
            "age": age,
            "age_from": age_from,
            "age_to": age_to,
            "price_from": price_from,
            "price_to": price_to,
            "sort": sort,
            "language": consult_lang,
            "min_rating": min_rating,
        },
        "filter_options": filter_options,
        "specialization_chips": specialization_chips,
        "all_specializations_url": all_specializations_url,
        "all_tutors_url": all_tutors_url,
        "active_filter_chips": active_filter_chips,
        "specialist_query_without_page": specialist_query_params.urlencode(),
        "reset_filters_url": request.path,
        "results_count_label": results_count_label,
        "language": language,
        "seo_title": _("Педагоги и специалисты для детей — KidsMap"),
        "meta_description": _("Найдите репетитора, педагога, психолога, логопеда, тренера или другого специалиста для ребёнка."),
        "specialist_breadcrumb_items": [
            {"name": str(_("Главная")), "url": reverse("home") if language == "az" else f"/{language}/"},
            {"name": str(_("Педагоги и специалисты")), "url": reverse("specialist_list") if spec_code else None},
        ] + ([{"name": next((s["label"] for s in filter_options.specializations if s["value"] == spec_code), spec_code), "url": None}] if spec_code else []),
    }
    return render(request, "catalog/specialist_list.html", context)

def specialist_detail(request, slug):
    require_specialists_section_enabled()

    from catalog.models import Specialist, SpecialistReview, SpecialistPracticeLocation
    from catalog.services.public_urls import build_public_absolute_uri
    from django.db.models import Prefetch

    specialist = get_object_or_404(
        Specialist.objects.prefetch_related(
            "specializations",
            Prefetch('practice_locations', queryset=SpecialistPracticeLocation.objects.filter(is_active=True)
                     .select_related('place', 'region', 'district', 'metro')),
            "documents",
        ),
        slug=slug,
        status=Specialist.STATUS_PUBLISHED,
        is_active=True
    )

    from catalog.services.content_quality import public_review_queryset
    reviews = public_review_queryset(specialist.reviews.all()).order_by("-created_at")
    reviews_count = reviews.count()
    if specialist.rating_count != reviews_count:
        specialist.refresh_rating_stats()

    visible_documents = specialist.documents.filter(
        document_type__in=["diploma", "certificate"],
        status="approved",
        is_published=True, opted_in_by_id=specialist.verified_person_user_id,
        opted_in_at__isnull=False, opted_in_by__is_active=True,
    )
    if not specialist.verified_person_user_id or not specialist.person_verified_at:
        visible_documents = visible_documents.none()

    language = (request.LANGUAGE_CODE or "az").split("-")[0]

    seo_title = f"{specialist.name} — {', '.join(spec.name_i18n(language) for spec in specialist.specializations.all())}"
    meta_description = f"{specialist.name_alt or specialist.name}: {specialist.bio_i18n(language)[:150]}"

    has_coords = any(loc.lat is not None and loc.lng is not None for loc in specialist.practice_locations.all())

    context = {
        "specialist": specialist,
        "reviews": reviews,
        "visible_documents": visible_documents,
        "language": language,
        "seo_title": seo_title,
        "seo_image_url": build_public_absolute_uri(request, specialist.photo.url) if specialist.photo else "",
        "meta_description": meta_description,
        "has_coords": has_coords,
        "google_maps_api_key": settings.GOOGLE_MAPS_API_KEY,
    }
    from catalog.services.specialist_presentation import public_profile_context
    from catalog.services.specialist_documents import is_person
    context.update(public_profile_context(specialist))
    context['can_manage_specialist'] = is_person(request.user, specialist)
    context['claim_workspace_url'] = reverse('specialist_workspace_claims', args=[specialist.pk])
    return render(request, "catalog/specialist_detail.html", context)

@require_POST
def add_specialist_review(request, pk):
    require_specialists_section_enabled()

    from catalog.models import Specialist, SpecialistReview
    from catalog.services.review_moderation import moderate_review_content
    from django.contrib import messages

    specialist = get_object_or_404(Specialist, pk=pk, status=Specialist.STATUS_PUBLISHED, is_active=True)

    if not request.user.is_authenticated:
        return _engagement_login_required_response(request, f"{specialist.get_absolute_url()}#reviews")

    rating_raw = (request.POST.get("rating") or "").strip()
    review_text = (request.POST.get("text") or "").strip()

    if not rating_raw:
        return _review_submission_response(request, ok=False, message=_("Выберите оценку от 1 до 5, чтобы отправить отзыв."),
                                           redirect_url=f"{specialist.get_absolute_url()}#reviews")

    try:
        rating = int(rating_raw)
    except (TypeError, ValueError):
        return _review_submission_response(request, ok=False, message=_("Оценка должна быть числом от 1 до 5."),
                                           redirect_url=f"{specialist.get_absolute_url()}#reviews")

    if rating < 1 or rating > 5:
        return _review_submission_response(request, ok=False, message=_("Оценка вне диапазона. Укажите значение от 1 до 5."),
                                           redirect_url=f"{specialist.get_absolute_url()}#reviews")

    if not review_text:
        return _review_submission_response(request, ok=False, message=_("Добавьте текст отзыва, чтобы другим пользователям было полезно ваше мнение."),
                                           redirect_url=f"{specialist.get_absolute_url()}#reviews")

    if len(review_text) > 5000:
        return _review_submission_response(request, ok=False, message=_("Текст отзыва слишком длинный. Сократите его до 5000 символов."),
                                           redirect_url=f"{specialist.get_absolute_url()}#reviews")

    author_name = ""
    if request.user.is_authenticated:
        candidates = (
            request.user.get_full_name(),
            request.user.get_username(),
            getattr(request.user, "email", ""),
        )
        for value in candidates:
            value = (value or "").strip()
            if value:
                author_name = value[:80]
                break
    if not author_name:
        author_name = _("Гость")

    moderated = moderate_review_content(author_name=author_name, text=review_text)

    defaults = {
        "rating": rating,
        "text": moderated.text,
        "author_name": moderated.author_name,
        "status": SpecialistReview.STATUS_PENDING,
        'submitted_at': timezone.now(), 'moderated_at': None, 'moderated_by': None,
        "is_approved": False,
        "rejection_reason": "",
    }

    from catalog.services.review_versions import submit_review, ReviewCooldown
    try:
        review_obj, revision = submit_review(target=specialist, user=request.user,
            rating=rating, text=moderated.text, author_name=moderated.author_name,
            contains_profanity=moderated.contains_profanity, enforce_cooldown=False)
    except ReviewCooldown as exc:
        from catalog.services.place_review_submission import cooldown_payload
        response = JsonResponse({'ok': False, 'cooldown': cooldown_payload(exc.next_allowed_at)}, status=429)
        response['Retry-After'] = str(cooldown_payload(exc.next_allowed_at)['retry_after'])
        return response

    from catalog.services.moderation_sla import submission_message
    message = submission_message('review')
    if moderated.contains_profanity:
        message = f"{message} {_('Нецензурные слова были автоматически скрыты.')}"

    return _review_submission_response(request, ok=True, message=message,
                                       redirect_url=f"{specialist.get_absolute_url()}#reviews")

def owner_specialist_create(request):
    require_specialists_section_enabled()

    if not request.user.is_authenticated:
        return _redirect_to_login(request)

    if request.method == "POST":
        form_action = (request.POST.get("form_action") or "").strip()
        draft_save_only = form_action == "save_draft"
        form = OwnerSpecialistForm(request.POST, request.FILES, draft_save_only=draft_save_only)
        result = save_owner_specialist_profile(user=request.user, form=form, draft_save_only=draft_save_only)
        if result.ok:
            messages.success(request, result.message)
            return redirect("owner_places_dashboard")
        form = result.form or form
    else:
        form = OwnerSpecialistForm()

    specializations = form.fields["specializations"].queryset.order_by("order", "name_ru")
    return render(
        request,
        "pages/owner_specialist_create.html",
        {
            "form": form,
            "specialist": None,
            "specializations": specializations,
            "meta_description": _("Добавление специалиста в каталог KidsMap."),
        },
    )

def owner_specialist_edit(request, pk):
    require_specialists_section_enabled()

    if not request.user.is_authenticated:
        return _redirect_to_login(request)

    specialist = get_object_or_404(Specialist, pk=pk, verified_person_user=request.user,
                                  verified_person_user__is_active=True, person_verified_at__isnull=False)

    if request.method == "POST":
        form_action = (request.POST.get("form_action") or "").strip()
        draft_save_only = form_action == "save_draft"
        form = OwnerSpecialistForm(
            request.POST,
            request.FILES,
            instance=specialist,
            draft_save_only=draft_save_only,
        )
        result = save_owner_specialist_profile(user=request.user, form=form, draft_save_only=draft_save_only)
        if result.ok:
            messages.success(request, result.message)
            return redirect("owner_places_dashboard")
        form = result.form or form
    else:
        form = OwnerSpecialistForm(instance=specialist)

    specializations = form.fields["specializations"].queryset.order_by("order", "name_ru")
    return render(
        request,
        "pages/owner_specialist_create.html",
        {
            "form": form,
            "specialist": specialist,
            "specializations": specializations,
            "meta_description": _("Редактирование профиля специалиста KidsMap."),
        },
    )
