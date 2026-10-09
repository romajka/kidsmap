"""Public directory: only approved networks and current published affiliations."""
from urllib.parse import urlencode
from django.core.paginator import Paginator
from django.db.models import Count, F, Q
from django.shortcuts import render
from django.views.decorators.http import require_GET
from catalog.models import Organization, Place
from catalog.services.content_quality import published_place_queryset
from catalog.services.locations import get_all_districts_flat_choices
from catalog.services.public_presentation import language_code, public_url, translated


COPY = {
    'ru': dict(title='Организации', intro='Найдите свою сеть — выберите удобный филиал', description='Образовательные центры, творческие студии и спортивные сети. Все опубликованные филиалы организации — на одной странице.', search='Название или направление', district='Район / регион', all='Все районы', submit='Найти', results='Организаций найдено', branches='Филиалов', photos='Фотографии филиалов', empty_branches='Филиалы пока не добавлены', open='Об организации и филиалах', empty='Ничего не нашли', empty_text='Попробуйте другое название или выберите другой район.', reset='Сбросить фильтры', previous='Назад', next='Далее', fallback='Часть текста показана на азербайджанском.', network_tag='Сеть центров', network_banner_title='Единая сеть филиалов', network_banner_sub='Один бренд — удобные локации по всему городу', view_network='Смотреть сеть и филиалы'),
    'az': dict(title='Təşkilatlar', intro='Uyğun şəbəkəni tapın — rahat filial seçin', description='Təhsil mərkəzləri, yaradıcılıq studiyaları və idman şəbəkələri. Təşkilatın bütün dərc edilmiş filialları bir səhifədə.', search='Ad və ya istiqamət', district='Rayon / region', all='Bütün rayonlar', submit='Axtar', results='Tapılan təşkilatlar', branches='Filiallar', photos='Filialların fotoları', empty_branches='Filiallar hələ əlavə edilməyib', open='Təşkilat və filiallar haqqında', empty='Nəticə tapılmadı', empty_text='Başqa ad və ya rayon seçməyə çalışın.', reset='Filtrləri sıfırla', previous='Geri', next='İrəli', fallback='Mətnin bir hissəsi azərbaycanca göstərilir.', network_tag='Mərkəzlər şəbəkəsi', network_banner_title='Vahid filial şəbəkəsi', network_banner_sub='Bir brend — şəhər boyu rahat məkanlar', view_network='Şəbəkəyə və filiallara bax'),
    'en': dict(title='Organizations', intro='Find your network — choose a nearby branch', description='Education centers, creative studios and sports networks. Explore every published branch of an organization in one place.', search='Name or activity', district='District / region', all='All districts', submit='Search', results='Organizations found', branches='Branches', photos='Branch photos', empty_branches='No branches added yet', open='Organization and branches', empty='No organizations found', empty_text='Try another name or choose a different district.', reset='Reset filters', previous='Previous', next='Next', fallback='Some text is shown in Azerbaijani.', network_tag='Network of centers', network_banner_title='Unified branch network', network_banner_sub='One brand — convenient locations across the city', view_network='View network and branches'),
}


def confirmed_branches():
    return published_place_queryset(Place.objects.all()).filter(
        organization_relationship_kind__in=('business', 'informational'),
        organization_join_place_ownership_version=F('ownership_version'),
        organization_join_org_ownership_version=F('organization__ownership_version'),
        organization__status='published', organization__approved_at__isnull=False,
        organization__archived_at__isnull=True,
    )


@require_GET
def organization_list(request):
    from catalog.services.features import require_organizations_section_enabled
    require_organizations_section_enabled()
    lang = language_code(getattr(request, 'LANGUAGE_CODE', 'az'))
    text = COPY[lang]
    query = request.GET.get('q', '').strip()[:200]
    district = request.GET.get('district', '').strip()[:100]
    districts = get_all_districts_flat_choices(lang)
    labels = dict(districts)
    organizations = Organization.objects.filter(status='published', approved_at__isnull=False, archived_at__isnull=True)
    if query:
        match = Q()
        for code in ('az', 'ru', 'en'):
            match |= Q(**{f'name_{code}__icontains': query}) | Q(**{f'description_{code}__icontains': query})
        organizations = organizations.filter(match)
    branches = confirmed_branches()
    if district:
        organizations = organizations.filter(pk__in=branches.filter(district=district).values('organization_id')) if district in labels else organizations.none()
    page = Paginator(organizations.order_by(f'name_{lang}', 'name_az', 'pk'), 12).get_page(request.GET.get('page'))
    ids = [org.pk for org in page]
    totals = dict(branches.filter(organization_id__in=ids).values('organization_id').annotate(total=Count('pk')).values_list('organization_id', 'total'))
    regions = {}
    for org_id, key in branches.filter(organization_id__in=ids).values_list('organization_id', 'district').distinct():
        if key in labels:
            regions.setdefault(org_id, set()).add(labels[key])
    # Window limit keeps thumbnail fetching bounded even for large networks.
    from django.db.models import Window
    from django.db.models.functions import RowNumber
    pictures = {}
    candidates = branches.filter(organization_id__in=ids).exclude(photo='', cover_photo='').annotate(
        row=Window(expression=RowNumber(), partition_by=[F('organization_id')], order_by=F('pk').asc())
    ).filter(row__lte=3)
    for place in candidates:
        if place.public_image_url:
            pictures.setdefault(place.organization_id, []).append({'url': place.public_image_url, 'name': translated(place, 'name', lang)[0]})
    cards = []
    for org in page:
        name, name_lang = translated(org, 'name', lang)
        description, description_lang = translated(org, 'description', lang)
        districts_list = sorted(regions.get(org.pk, []))
        cards.append(dict(name=name, name_language=name_lang, description=description, description_language=description_lang,
            fallback=name_lang != lang or bool(description and description_lang != lang), url=public_url(org, lang),
            branch_count=totals.get(org.pk, 0), districts=districts_list,
            districts_preview=districts_list[:3], districts_extra_count=max(0, len(districts_list) - 3),
            photos=pictures.get(org.pk, [])))
    params = {key: value for key, value in [('q', query), ('district', district)] if value}
    def page_url(number):
        return '?' + urlencode({**params, 'page': number})
    return render(request, 'catalog/organization_list.html', dict(
        text=text, seo_title=f"{text['title']} — KidsMap", meta_description=text['description'],
        q=query, district=district, districts=districts, cards=cards, page_obj=page,
        previous_url=page_url(page.previous_page_number()) if page.has_previous() else '',
        next_url=page_url(page.next_page_number()) if page.has_next() else '',
    ))
