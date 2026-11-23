"""Admin editors for the additive business hierarchy.

Content is proposed through publication; structure is created through its
locked model services. Review and visibility are explicit POST actions.
"""
from operator import mod

from django import forms
from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404, HttpResponseRedirect
from django.urls import path, reverse
from django.db.models import Count, Q
from django.utils.functional import lazy
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods

from catalog.models import Activity, OfferingGroup, Organization, Place, Program, VolunteerPlaceRevision
from catalog.services import publication
from catalog.services.staff_roles import is_volunteer


class CandidateForm(forms.ModelForm):
    source_version = forms.IntegerField(widget=forms.HiddenInput, required=False)
    candidate_version = forms.IntegerField(widget=forms.HiddenInput, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            kind = 'offering_group' if self._meta.model is OfferingGroup else self._meta.model.__name__.lower()
            revision = VolunteerPlaceRevision.objects.filter(**{kind: self.instance}).first()
            self.fields['source_version'].initial = self.instance.content_version
            self.fields['candidate_version'].initial = revision.version if revision else 0
            if revision and revision.status in {'draft', 'pending', 'rejected'}:
                for key, value in revision.payload.items():
                    if key in self.fields:
                        self.initial[key] = value
        else:
            self.fields['source_version'].initial = 0
            self.fields['candidate_version'].initial = 0

    def clean(self):
        data = super().clean()
        if self.instance.pk and data.get('source_version') is None:
            raise ValidationError(_('Версия формы отсутствует. Обновите страницу.'))
        if data.get('candidate_version') is None:
            raise ValidationError(_('Версия черновика отсутствует. Обновите страницу.'))
        return data


# Keep both translation and percent formatting deferred until rendering.
_format_label = lazy(mod, str)


from catalog.services.phone_forms import ContactPhoneFormMixin


class OrganizationForm(ContactPhoneFormMixin, CandidateForm):
    whatsapp_same_as_phone = forms.BooleanField(required=False, label=_('WhatsApp на этом же номере'))

    def clean(self):
        data = super().clean()
        if data.get('whatsapp_same_as_phone'):
            if data.get('phone'):
                data['whatsapp'] = data['phone']
            elif 'phone' not in self.errors:
                self.add_error('phone', _('Укажите телефон для WhatsApp.'))
        return data

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ('logo', 'cover_photo'):
            value = self.initial.get(name)
            if name in self.fields and isinstance(value, str):
                model_field = self.instance._meta.get_field(name)
                self.initial[name] = model_field.attr_class(self.instance, model_field, value)
        # View-only admin (a moderator who is not the owner) builds the form
        # without editable fields; it must still open, not crash.
        if 'name_az' in self.fields:
            self.fields['name_az'].required = True
            self.fields['name_az'].widget.attrs['aria-required'] = 'true'
        if self.is_bound and 'whatsapp' in self.fields:
            checkbox = self.fields['whatsapp_same_as_phone'].widget
            if checkbox.value_from_datadict(self.data, self.files, self.add_prefix('whatsapp_same_as_phone')):
                self.data = self.data.copy()
                self.data[self.add_prefix('whatsapp')] = ''

    def _clean_media(self, name):
        from catalog.controllers.organization_workspace import MEDIA_RULES, MEDIA_FORMATS
        upload = self.cleaned_data.get(name)
        if not upload or getattr(upload, '_committed', True) and not hasattr(upload, 'image'):
            return upload
        limit, min_w, min_h = MEDIA_RULES[name]
        if upload.size > limit:
            raise ValidationError(_('Файл больше %(mb)s МБ.') % {'mb': limit // (1024 * 1024)})
        image = getattr(upload, 'image', None)
        if getattr(image, 'format', None) not in MEDIA_FORMATS:
            raise ValidationError(_('Загрузите JPG, PNG или WebP.'))
        width, height = getattr(image, 'size', (0, 0))
        if width < min_w or height < min_h:
            raise ValidationError(_('Изображение слишком маленькое: нужно от %(w)s×%(h)s px.') % {'w': min_w, 'h': min_h})
        return upload

    def clean_logo(self):
        return self._clean_media('logo')

    def clean_cover_photo(self):
        return self._clean_media('cover_photo')

    def _clean_social(self, name):
        from catalog.services.organization_state import normalize_social
        try:
            return normalize_social(name, self.cleaned_data.get(name))
        except ValueError:
            raise ValidationError(_('Укажите ссылку на профиль или @имя аккаунта.'))

    def clean_instagram(self):
        return self._clean_social('instagram')

    def clean_facebook(self):
        return self._clean_social('facebook')

    def clean_tiktok(self):
        return self._clean_social('tiktok')

    class Meta:
        model = Organization
        fields = ('name_az', 'name_ru', 'name_en', 'description_az', 'description_ru', 'description_en', 'phone', 'whatsapp', 'whatsapp_same_as_phone', 'website',
                  'address', 'instagram', 'facebook', 'tiktok', 'logo', 'cover_photo')
        labels = {**{f'name_{lang}':_format_label(_('Название организации (%(language)s)'), {'language':lang.upper()}) for lang in ('az','ru','en')},
            **{f'description_{lang}':_format_label(_('Описание организации (%(language)s)'), {'language':lang.upper()}) for lang in ('az','ru','en')},
            'phone':_('Общий телефон организации'),'whatsapp':_('Общий WhatsApp организации'),'website':_('Сайт организации'),
            'address':_('Адрес головного офиса'),'logo':_('Логотип'),'cover_photo':_('Обложка')}
        widgets = {
            **{f'description_{lang}': forms.Textarea(attrs={'rows': 4}) for lang in ('az', 'ru', 'en')},
            'phone': forms.TextInput(attrs={'inputmode': 'tel'}),
            'whatsapp': forms.TextInput(attrs={'inputmode': 'tel'}),
        }
        help_texts = {'phone':_('Показывается в карточках филиалов, у которых нет своего телефона.'),
            'website':_('Используется в филиале, если там не указан собственный сайт.'),
            'instagram':_('Ссылка на профиль или @имя аккаунта.'),'facebook':_('Ссылка на профиль или @имя аккаунта.'),
            'tiktok':_('Ссылка на профиль или @имя аккаунта.'),
            'logo':_('Квадрат от 120 px, JPG/PNG/WebP, до 5 МБ.'),'cover_photo':_('От 800×300 px, JPG/PNG/WebP, до 8 МБ.'),
            'name_az':_('Укажите название, под которым родители знают организацию.'),
            'name_ru':_('Если пусто — на русской версии сайта покажем азербайджанское название.'),
            'name_en':_('Если пусто — на английской версии сайта покажем азербайджанское название.'),
            'description_az':_('Расскажите, чем занимается организация и для какого возраста подходят занятия.'),
            'address':_('Адрес главного офиса. Адреса филиалов указываются в карточках мест.'),
            'whatsapp':_('Показывается на странице организации как кнопка WhatsApp.')}


class ProgramForm(CandidateForm):
    class Meta:
        model = Program
        fields = ('organization', 'category', 'subcategory', 'name_az', 'name_ru', 'name_en', 'description_az', 'description_ru', 'description_en')


class ActivityForm(CandidateForm):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        if self.instance.program_id:
            for name in ('category','subcategory'):self.fields[name].disabled=True

    class Meta:
        model = Activity
        fields = ('place', 'program', 'category', 'subcategory', 'name_az', 'name_ru', 'name_en', 'description_az', 'description_ru', 'description_en', 'supplement_az', 'supplement_ru', 'supplement_en')


class OfferingGroupForm(CandidateForm):
    class Meta:
        model = OfferingGroup
        fields = ('activity', 'name_az', 'name_ru', 'name_en', 'age_from', 'age_to', 'lesson_format', 'language', 'schedule_text', 'teachers_text', 'conditions_az', 'conditions_ru', 'conditions_en')


class PublicationStatusFilter(admin.SimpleListFilter):
    title = _('Статус публикации')
    parameter_name = 'status'

    def lookups(self, request, model_admin):
        from catalog.models.catalog_structure import PublicationState
        return PublicationState.choices

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(status=self.value())
        return queryset


def organization_status_filter(value):
    """Publication and candidate review are independent dimensions."""
    pending = (Q(content_revision__status='pending') | Q(status='pending')) & Q(archived_at__isnull=True)
    if value == 'pending':
        return pending
    if value == 'published':
        return Q(status='published', approved_at__isnull=False, archived_at__isnull=True)
    if value == 'draft':
        return Q(status='draft') & ~pending
    if value == 'inconsistent':
        # Legacy rows: marked published but never approved, so never public.
        return Q(status='published', approved_at__isnull=True, archived_at__isnull=True) & ~pending
    return Q(status=value)


class OrganizationPublicationStatusFilter(PublicationStatusFilter):
    def lookups(self, request, model_admin):
        return (*super().lookups(request, model_admin), ('inconsistent', _('Требуют решения')))

    def queryset(self, request, queryset):
        return queryset.filter(organization_status_filter(self.value())) if self.value() else queryset


class OrganizationHasBranchesFilter(admin.SimpleListFilter):
    title = _('Филиалы')
    parameter_name = 'has_branches'

    def lookups(self, request, model_admin):
        return (
            ('yes', _('Есть филиалы')),
            ('no', _('Без филиалов')),
            ('stale', _('Есть неактуальные связи')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'stale':
            from catalog.models import Place
            from catalog.services.organization_state import current_branch_q
            stale = Place.objects.filter(organization__isnull=False, deleted_at__isnull=True).exclude(current_branch_q())
            return queryset.filter(pk__in=stale.values('organization_id'))
        if self.value() == 'yes':
            return queryset.filter(places__isnull=False, places__deleted_at__isnull=True).distinct()
        if self.value() == 'no':
            return queryset.exclude(places__deleted_at__isnull=True, places__isnull=False)
        return queryset


class OrganizationFilter(admin.SimpleListFilter):
    title = _('Организация')
    parameter_name = 'organization'

    def lookups(self, request, model_admin):
        return [(org.pk, org.name_ru or org.name_az or org.name_en) for org in Organization.objects.filter(archived_at__isnull=True).order_by('pk')]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(organization_id=self.value())
        return queryset


class CategoryFilter(admin.SimpleListFilter):
    title = _('Рубрика')
    parameter_name = 'category'

    def lookups(self, request, model_admin):
        from catalog.models import Category
        return [(cat.code, cat.name_ru or cat.name) for cat in Category.objects.filter(is_active=True).order_by('order', 'name')]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(category_id=self.value())
        return queryset


class PlaceFilter(admin.SimpleListFilter):
    title = _('Место / Филиал')
    parameter_name = 'place'

    def lookups(self, request, model_admin):
        from catalog.models import Place
        return [(p.pk, p.name_ru or p.name_az or p.name) for p in Place.objects.filter(deleted_at__isnull=True).order_by('name')]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(place_id=self.value())
        return queryset


class LessonFormatFilter(admin.SimpleListFilter):
    title = _('Формат занятия')
    parameter_name = 'lesson_format'

    def lookups(self, request, model_admin):
        return [('group', _('Групповой')), ('individual', _('Индивидуальный'))]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(lesson_format=self.value())
        return queryset


class BusinessEditor(admin.ModelAdmin):
    change_form_template = 'admin/catalog/business/change_form.html'
    actions = None
    @property
    def publication_kind(self):
        return 'offering_group' if self.opts.model_name == 'offeringgroup' else self.opts.model_name
    readonly_fields = ('publication_badge', 'ownership_badge', 'verified_badge', 'data_version', 'archived_since')
    list_display = ('display_name', 'publication_badge', 'display_content_version', 'display_updated_at')
    search_fields = ('name_az', 'name_ru', 'name_en')
    list_filter = (PublicationStatusFilter,)
    ordering = ('-updated_at',)

    def has_module_permission(self, request):
        return request.user.is_staff and not is_volunteer(request.user) and super().has_module_permission(request)

    def has_add_permission(self, request):
        return not is_volunteer(request.user) and super().has_add_permission(request)

    def has_change_permission(self, request, obj=None):
        if is_volunteer(request.user) or not super().has_change_permission(request, obj):
            return False
        if obj is None:
            return True
        from catalog.services.business_team import has_action
        action = {'organization': 'organization.edit', 'program': 'program.manage', 'activity': 'place.edit', 'offeringgroup': 'place.edit'}[self.opts.model_name]
        return has_action(user=request.user, target=obj, action=action)

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description=_('Название'))
    def display_name(self, obj):
        return obj.name_az or obj.name_ru or obj.name_en or f'#{obj.pk}'

    @admin.display(description=_('Публикация'))
    def publication_badge(self, obj):
        if isinstance(obj, OfferingGroup):
            status = getattr(obj.activity, 'status', 'draft')
            status_text = _('Публикация занятия: %(status)s') % {'status': obj.activity.get_status_display()}
            return format_html('<span class="km-status-badge km-status-{}">{}</span>', status, status_text)
        status = getattr(obj, 'status', 'draft')
        status_text = obj.get_status_display() if hasattr(obj, 'get_status_display') else status
        return format_html('<span class="km-status-badge km-status-{}">{}</span>', status, status_text)

    @admin.display(description=_('Владение'))
    def ownership_badge(self, obj):
        target = obj if isinstance(obj, Organization) else (obj.organization if isinstance(obj, Program) else (obj.activity.place if isinstance(obj, OfferingGroup) else obj.place))
        if target.owner_id:
            owner_name = target.owner.get_full_name() or target.owner.username
            return format_html('<span class="km-status-badge km-status-published" title="{}">{}</span>', target.owner.email or owner_name, owner_name)
        return format_html('<span class="km-status-badge km-status-draft">{}</span>', _('Не назначен'))

    @admin.display(description=_('Проверка данных'))
    def verified_badge(self, obj):
        if isinstance(obj, Organization):
            if obj.ownership_verified_at:
                return format_html('<span class="km-status-badge km-status-published">{}</span>', _('Владение проверено'))
            return format_html('<span class="km-status-badge km-status-draft">{}</span>', _('Владение не проверено'))
        if isinstance(obj, OfferingGroup):
            if obj.conditions_verified_at:
                return format_html('<span class="km-status-badge km-status-published">{}</span>', _('Условия подтверждены'))
            return format_html('<span class="km-status-badge km-status-draft">{}</span>', _('Условия не подтверждены'))
        return format_html('<span class="km-status-badge km-status-draft">{}</span>', _('Отдельный статус проверки не установлен'))

    @admin.display(description=_('Версия'), ordering='content_version')
    def display_content_version(self, obj):
        return obj.content_version

    @admin.display(description=_('Версия данных'))
    def data_version(self, obj):
        return obj.content_version

    @admin.display(description=_('В архиве с'))
    def archived_since(self, obj):
        from django.utils import timezone
        return timezone.localtime(obj.archived_at).strftime('%d.%m.%Y %H:%M') if obj.archived_at else '—'

    @admin.display(description=_('Обновлено'), ordering='-updated_at')
    def display_updated_at(self, obj):
        from django.utils import timezone
        local = timezone.localtime(obj.updated_at)
        return format_html('<span class="km-org-updated">{}</span>', local.strftime('%d.%m.%Y %H:%M'))

    def get_readonly_fields(self, request, obj=None):
        return self.readonly_fields if obj else ('publication_badge', 'ownership_badge', 'verified_badge')

    def get_fields(self, request, obj=None):
        fields = list(self.form._meta.fields)
        if obj is not None:
            fields = [name for name in fields if name not in self.structural_fields]
        return ['publication_badge', 'ownership_badge', 'verified_badge', *fields, 'source_version', 'candidate_version', 'data_version', 'archived_since'] if obj else [*fields, 'source_version', 'candidate_version']

    def get_fieldsets(self, request, obj=None):
        available = set(self.get_fields(request, obj))
        sections = []
        for title, names in self.editor_sections:
            fields = tuple(name for name in names if name in available)
            if fields:
                sections.append((title, {'fields': fields, 'classes': ('km-business-section',)}))
                available.difference_update(fields)
        badges = tuple(name for name in ('publication_badge', 'ownership_badge', 'verified_badge') if name in available)
        if badges:
            sections.insert(0, (_('Состояние'), {'fields': badges, 'classes': ('km-business-section',)}))
            available.difference_update(badges)
        versions = tuple(name for name in ('source_version', 'candidate_version', 'data_version', 'archived_since') if name in available)
        available.difference_update(versions)
        if available:
            sections.append((None, {'fields': tuple(sorted(available))}))
        if versions and sections:
            # Hidden versions travel with a useful section, never an empty tab.
            sections[0][1]['fields'] += versions
        return sections

    def get_urls(self):
        base = super().get_urls()
        name = f'{self.opts.app_label}_{self.opts.model_name}'
        extra = [
            path('<path:object_id>/transition/', self.admin_site.admin_view(self.transition_view), name=f'{name}_transition'),
        ]
        if self.model is Organization:
            extra.append(path('search-suggestions/', self.admin_site.admin_view(self.search_suggestions_view), name=f'{name}_search_suggestions'))
        return extra + base

    def search_suggestions_view(self, request):
        if not self.has_view_or_change_permission(request):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied
        from django.http import JsonResponse
        from django.urls import reverse
        term = (request.GET.get("q") or "").strip()
        if len(term) < 2:
            return JsonResponse({"results": []})
        language_code = getattr(request, "LANGUAGE_CODE", None)

        variants = list(dict.fromkeys([term, term.lower(), term.capitalize(), term.upper()]))
        q_filter = Q()
        fields = self.search_fields
        for v in variants:
            for fld in fields:
                q_filter |= Q(**{f"{fld}__icontains": v})

        queryset = self.get_queryset(request).filter(q_filter).distinct()[:8]

        results = []
        for org in queryset:
            title = (getattr(org, f"name_{language_code}", None) or org.name_ru or org.name_az or org.name_en or "").strip()
            if not title:
                continue

            meta_parts = []
            if org.phone:
                meta_parts.append(str(org.phone))
            if org.address:
                meta_parts.append(org.address)
            if org.website:
                meta_parts.append(str(org.website))

            owner_label = ""
            if org.owner:
                owner_label = org.owner.get_username() or getattr(org.owner, "email", "")
                if owner_label:
                    meta_parts.append(str(owner_label))

            change_url = reverse("admin:catalog_organization_change", args=[org.pk])

            tone = "muted"
            if org.status == "published":
                tone = "good"
            elif org.status == "pending":
                tone = "warn"
            elif org.status == "rejected":
                tone = "danger"

            results.append(
                {
                    "id": org.pk,
                    "value": title,
                    "label": title,
                    "meta": " • ".join(part for part in meta_parts if part)[:180],
                    "status": org.status,
                    "status_label": org.get_status_display(),
                    "status_tone": tone,
                    "category": str(_("Организация")),
                    "district": "",
                    "address": org.address,
                    "phone": str(org.phone or ""),
                    "owner": owner_label,
                    "change_url": change_url,
                    "public_url": "",
                }
            )

        return JsonResponse(
            {
                "results": results,
                "labels": {
                    "edit": str(_("Редактировать организацию")),
                    "found": str(_("Найдено")),
                },
            }
        )

    def get_form(self, request, obj=None, **kwargs):
        form_class = super().get_form(request, obj, **kwargs)
        error = getattr(request, '_business_save_error', None)
        if error is None:
            return form_class

        class BoundErrorForm(form_class):
            def clean(self):
                data = super().clean()
                if hasattr(error, 'error_dict'):
                    for name, errors in error.error_dict.items():
                        self.add_error(name if name in self.fields else None, errors)
                else:
                    self.add_error(None, error)
                return data
        return BoundErrorForm

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        context = dict(extra_context or {})
        obj = self.get_object(request, object_id) if object_id else None
        context['km_business_kind'] = self.publication_kind
        context['km_business_object'] = obj
        if obj:
            from catalog.services.business_team import platform_has_action

            context['km_business_revision'] = VolunteerPlaceRevision.objects.filter(**{self.publication_kind: obj}).first()
            revision = context['km_business_revision']
            can_review = not obj.archived_at and platform_has_action(user=request.user, action='place.publish')
            context['km_business_can_approve'] = can_review and revision is not None and revision.status == 'pending'
            context['km_business_can_unpublish'] = (
                can_review and not isinstance(obj, OfferingGroup) and obj.status == 'published'
                and (not isinstance(obj, Organization) or obj.approved_at is not None)
                and (revision is None or revision.status not in {'draft', 'pending'})
            )
            if revision and revision.status in {'draft', 'pending', 'rejected'}:
                current = publication.snapshot(obj, self.publication_kind)
                context['km_business_changes'] = [
                    {'label': self.form.base_fields[name].label or obj._meta.get_field(name).verbose_name,
                     'current': current.get(name), 'candidate': revision.payload[name]}
                    for name in revision.changed_fields
                    if name in revision.payload and name in self.form._meta.fields
                ]
            context['km_business_transition_url'] = reverse(f'admin:{self.opts.app_label}_{self.opts.model_name}_transition', args=[obj.pk])
            from .navigation import business_navigation
            context['km_business_links'] = business_navigation(request, obj)
            if isinstance(obj, Organization):
                from catalog.services.organization_connections import organization_name

                context['km_business_organization_name'] = organization_name(obj)
                place_admin = self.admin_site._registry.get(Place)
                if not obj.archived_at and place_admin and place_admin.has_connection_permission(request):
                    context['km_business_connect_places_url'] = reverse('admin:catalog_place_organization_connections',
                        query={'organization_id': obj.pk})
            context['km_business_can_add_group'] = any('offeringgroup/add/' in url for _label, url in context['km_business_links'])
            context['km_business_can_invite'] = isinstance(obj, Organization) and obj.owner_id == request.user.pk
            if isinstance(obj, Activity):
                context['km_activity_groups'] = list(obj.offering_groups.filter(archived_at__isnull=True).order_by('pk'))
        try:
            return super().changeform_view(request, object_id, form_url, context)
        except ValidationError as exc:
            # The failed atomic save has rolled back. Rebind the same POST as an
            # invalid form, without redirecting away from the user's input.
            request._business_save_error = exc
            return super().changeform_view(request, object_id, form_url, context)

    def get_changeform_initial_data(self, request):
        from .navigation import authorized_initial
        return authorized_initial(request, self.model, super().get_changeform_initial_data(request))

    def related_links(self, obj):
        return []

    def save_model(self, request, obj, form, change):
        if not (self.has_change_permission(request, obj) if change else self.has_add_permission(request)):
            raise PermissionDenied
        if change:
            target = type(obj).objects.get(pk=obj.pk)
            if int(form.cleaned_data['source_version']) != target.content_version:
                raise ValidationError(_('Форма устарела. Обновите страницу.'))
        else:
            target = self.create_target(request, form.cleaned_data)
            obj.pk = target.pk
            obj._state.adding = False
            obj._state.db = target._state.db
        # Uploaded files must exist in storage before the candidate names them.
        from django.db.models import FileField
        for model_field in obj._meta.fields:
            if isinstance(model_field, FileField):
                value = getattr(obj, model_field.attname)
                if value and not getattr(value, '_committed', True):
                    value.save(value.name, value.file, save=False)
        patch = publication.snapshot(obj, self.publication_kind)
        patch = {key: value for key, value in patch.items() if key in publication.fields_for(self.publication_kind)}
        if isinstance(target,Activity) and target.program_id:
            for key in ('category','subcategory'):patch.pop(key,None)
        publication.propose(
            actor=request.user, target_type=self.publication_kind, target_id=target.pk,
            patch=patch, schema_version=publication.SCHEMA_VERSION,
            expected_version=target.content_version,
            revision_version=int(form.cleaned_data['candidate_version']),
            submit='_save_draft' not in request.POST, explicit_save=True,
        )
        obj.refresh_from_db()

    def save_related(self, request, form, formsets, change):
        # No inlines may bypass candidate publication.
        if formsets:
            raise ValidationError(_('Вложенные изменения требуют отдельного редактора.'))

    def response_add(self, request, obj, post_url_continue=None):
        return HttpResponseRedirect(reverse(f'admin:{self.opts.app_label}_{self.opts.model_name}_change', args=[obj.pk]))

    def response_change(self, request, obj):
        return HttpResponseRedirect(request.path)

    def transition_view(self, request, object_id):
        if request.method != 'POST':
            raise PermissionDenied
        obj = self.get_object(request, object_id)
        if obj is None or not self.has_view_permission(request, obj):
            raise PermissionDenied
        action = request.POST.get('action')
        try:
            if action == 'approve':
                revision = VolunteerPlaceRevision.objects.filter(**{self.publication_kind: obj}).first()
                if revision is None or revision.status != 'pending':
                    raise ValidationError(_('Нет заявки на проверке.'))
                publication.review(actor=request.user, revision_id=revision.pk, version=int(request.POST.get('revision_version', '-1')), approve=True)
            elif action == 'unpublish' and not isinstance(obj, OfferingGroup):
                publication.unpublish(actor=request.user, target_type=self.publication_kind,
                                      target_id=obj.pk, expected_version=int(request.POST.get('source_version', '-1')))
            elif action == 'return':
                revision = VolunteerPlaceRevision.objects.filter(**{self.publication_kind: obj}).first()
                if revision is None or revision.status != 'pending':
                    raise ValidationError(_('Нет заявки на проверке.'))
                note = (request.POST.get('review_note') or '').strip()
                if not note:
                    raise ValidationError(_('Напишите, что нужно исправить.'))
                publication.review(actor=request.user, revision_id=revision.pk,
                                   version=int(request.POST.get('revision_version', '-1')), approve=False, note=note)
            elif action == 'relink' and isinstance(obj, Organization):
                from catalog.services.organization_ownership import request_join
                request_join(actor=request.user, place_id=int(request.POST.get('place_id', '-1')),
                             organization_id=obj.pk, relationship_kind='informational')
            elif action == 'invite' and isinstance(obj, Organization):
                from catalog.services.business_team import invite
                invite(actor=request.user, target_type='organization', target_id=obj.pk,
                       email=request.POST.get('email', ''), role='EDITOR',
                       actions=['organization.view', 'organization.edit', 'program.manage'],
                       scope='all_network', place_ids=[])
            else:
                raise ValidationError(_('Неизвестное действие.'))
        except (ValueError, ValidationError) as exc:
            self.message_user(request, '; '.join(exc.messages) if isinstance(exc, ValidationError) else str(_('Неверная версия.')), level=messages.ERROR)
        else:
            self.message_user(request, _('Действие выполнено.'), level=messages.SUCCESS)
        return HttpResponseRedirect(reverse(f'admin:{self.opts.app_label}_{self.opts.model_name}_change', args=[obj.pk]))


@admin.register(Organization)
class OrganizationAdmin(BusinessEditor):
    change_list_template = "admin/catalog/organization/change_list.html"
    editor_sections = (
        ('profile', _('Основные данные'), ('name_az', 'description_az')),
        ('translations', _('Переводы на русский и английский'), ('name_ru', 'description_ru', 'name_en', 'description_en')),
        ('contacts', _('Контакты'), ('phone', 'whatsapp_same_as_phone', 'whatsapp', 'website', 'address')),
        ('media', _('Логотип и обложка'), ('logo', 'cover_photo')),
        ('social', _('Социальные сети'), ('instagram', 'facebook', 'tiktok')),
    )
    form = OrganizationForm
    change_form_template = 'admin/catalog/organization/change_form.html'
    structural_fields = frozenset()
    list_display = ('org_card', 'lifecycle_badge', 'readiness_badge', 'places_count_badge', 'ownership_badge', 'display_updated_at')
    list_display_links = ('org_card',)
    list_filter = (OrganizationPublicationStatusFilter, OrganizationHasBranchesFilter)
    search_fields = (
        'name_az', 'name_ru', 'name_en', 'address', 'phone', 'whatsapp', 'website',
        'owner__username', 'owner__email', 'owner__first_name', 'owner__last_name',
    )
    actions = ['mark_published', 'mark_draft']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('owner', 'content_revision')

    def get_fields(self, request, obj=None):
        return [field for field in super().get_fields(request, obj) if field not in ('data_version', 'archived_since')]

    # ── Changelist: one row tells a non-technical editor what it is and what to do.
    def _row_state(self, obj):
        from catalog.services.organization_state import lifecycle
        cache = self.__dict__.setdefault('_row_states', {})
        if obj.pk not in cache:
            cache[obj.pk] = lifecycle(obj, getattr(obj, 'content_revision', None))
        return cache[obj.pk]

    @admin.display(description=_('Название'), ordering='name_az')
    def org_card(self, obj):
        name = obj.name_az or obj.name_ru or obj.name_en or f'#{obj.pk}'
        second = obj.name_ru if obj.name_ru and obj.name_ru != name else (obj.name_en if obj.name_en and obj.name_en != name else '')
        logo = (format_html('<img src="{}" alt="" width="40" height="40" loading="lazy">', obj.logo.url) if obj.logo
                else format_html('<span>{}</span>', name[:1].upper()))
        return format_html('<span class="km-orgl-name"><span class="km-orgl-logo">{}</span><span class="km-orgl-text"><b>{}</b>{}</span></span>',
                           logo, name, format_html('<small>{}</small>', second) if second else '')

    @admin.display(description=_('Статус'))
    def lifecycle_badge(self, obj):
        state = self._row_state(obj)
        return format_html('<span class="km-orgl-state km-orgl-state--{}" data-org-state="{}" title="{}"><i></i>{}</span>',
                           state.tone, state.code, state.hint, state.label)

    @admin.display(description=_('Готовность'))
    def readiness_badge(self, obj):
        from catalog.services.organization_state import readiness, BranchHealth
        revision = getattr(obj, 'content_revision', None)
        data = dict(revision.payload) if revision and revision.status in ('draft', 'pending', 'rejected') else None
        current, _stale = getattr(self, '_branch_counts', {}).get(obj.pk, (0, 0))
        ready = readiness(obj, data=data, health=BranchHealth(current=[None] * current))
        missing = ', '.join(str(item['label']) for item in ready['items'] if not item['done'])
        return format_html('<span class="km-orgl-ready" title="{}"><span class="km-orgl-ready__bar"><span style="width:{}%"></span></span><b>{}%</b></span>',
                           (_('Не хватает: %(items)s') % {'items': missing}) if missing else _('Профиль заполнен'),
                           ready['percent'], ready['percent'])

    def get_list_display(self, request):
        from catalog.services.features import is_organizations_section_enabled

        site_enabled = is_organizations_section_enabled()

        @admin.display(description=_('Действия'))
        def row_action(obj):
            return self.organization_row_actions(request, obj, site_enabled=site_enabled)

        return (*self.list_display, row_action)

    def get_fieldsets(self, request, obj=None):
        sections = [
            (title, {'fields': fields, 'classes': (key,)})
            for key, title, fields in self.editor_sections
        ]
        sections[0][1]['fields'] += ('source_version', 'candidate_version')
        if obj:
            sections.append((_('Состояние и владение'), {
                'fields': (*self.readonly_fields,),
                'classes': ('status',),
            }))
        return sections

    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        form = context['adminform'].form
        errors = form.errors if form.is_bound else {}
        context['km_org_invalid_sections'] = {
            key for key, _title, fields in self.editor_sections if errors.keys() & set(fields)
        }
        return super().render_change_form(request, context, add, change, form_url, obj)

    def organization_row_actions(self, request, obj, *, site_enabled):
        from django.utils.html import format_html_join
        from catalog.services.organization_state import public_path

        state = self._row_state(obj)
        change = reverse('admin:catalog_organization_change', args=[obj.pk])
        can_edit = self.has_change_permission(request, obj)
        if state.review_pending and self.can_publish(request.user):
            main_label, change = _('Решить заявку'), change + '#km-publication'
        else:
            main_label = _('Редактировать') if can_edit else _('Открыть')
        links = [(change, main_label, 'km-orgl-act', '_self')]
        if not is_volunteer(request.user) and self.has_view_or_change_permission(request, obj):
            preview = reverse('admin:catalog_organization_site_preview', args=[obj.pk])
            links.append((preview, _('Предпросмотр'), 'km-orgl-act km-orgl-act--plain', '_blank'))
        if state.public and site_enabled:
            links.append((public_path(obj), _('На сайте'), 'km-orgl-act km-orgl-act--plain', '_blank'))
        return format_html(
            '<div class="km-orgl-actions">{}</div>',
            format_html_join('', '<a href="{}" class="{}" target="{}" rel="noopener">{}</a>',
                             ((url, css, target, label) for url, label, css, target in links)),
        )

    def get_urls(self):
        base = super().get_urls()
        preview = self.admin_site.admin_view(require_http_methods(['GET', 'HEAD', 'POST'])(self.site_preview))
        return [
            path('site-preview/', preview, name='catalog_organization_add_site_preview'),
            path('<int:object_id>/site-preview/', preview, name='catalog_organization_site_preview'),
        ] + base

    def site_preview(self, request, object_id=None):
        from catalog.services.organization_admin_preview import render_organization_preview

        obj = self.get_object(request, str(object_id)) if object_id is not None else None
        if object_id is not None and obj is None:
            raise Http404
        if is_volunteer(request.user):
            raise PermissionDenied
        if obj is None:
            allowed = request.method == 'POST' and self.has_add_permission(request)
        elif request.method == 'POST':
            allowed = self.has_change_permission(request, obj)
        else:
            allowed = self.has_view_or_change_permission(request, obj)
        if not allowed:
            raise PermissionDenied
        return render_organization_preview(request, obj, form_class=self.form)

    @admin.display(description=_('Филиалы'))
    def places_count_badge(self, obj):
        from catalog.services.organization_state import branch_counts_by_org
        current, stale = getattr(self, '_branch_counts', {}).get(obj.pk) or branch_counts_by_org([obj.pk])[obj.pk]
        url = reverse('admin:catalog_place_changelist') + f'?organization__id__exact={obj.pk}'
        if not current and not stale:
            return mark_safe('<span class="text-muted" style="font-size: 13px;">—</span>')
        html = format_html('<a href="{}" class="km-org-count-badge km-org-count-badge--branches" title="{}"><svg class="km-i" viewBox="0 0 960 960" aria-hidden="true"><use href="#kmi-place"></use></svg>{}</a>', url, _('Подтверждённые филиалы'), current)
        if stale:
            html += format_html(' <a href="{}" class="km-org-count-badge km-org-count-badge--stale" title="{}">⚠ {}</a>',
                                reverse('admin:catalog_organization_change', args=[obj.pk]) + '#km-org-branches', _('Связи ждут повторного подтверждения'), stale)
        return html

    def get_changelist_instance(self, request):
        cl = super().get_changelist_instance(request)
        from catalog.services.organization_state import branch_counts_by_org
        self._branch_counts = branch_counts_by_org([obj.pk for obj in cl.result_list])
        self._row_states = {}
        return cl

    @admin.display(description=_('Программы'))
    def programs_count_badge(self, obj):
        count = obj.programs.filter(archived_at__isnull=True).count()
        url = reverse('admin:catalog_program_changelist') + f'?organization__id__exact={obj.pk}'
        if count > 0:
            return format_html('<a href="{}" class="km-org-count-badge km-org-count-badge--programs" title="{}"><svg class="km-i" viewBox="0 0 960 960" aria-hidden="true"><use href="#kmi-school"></use></svg>{}</a>', url, _('Смотреть программы'), count)
        return mark_safe('<span class="text-muted" style="font-size: 13px;">—</span>')

    @admin.display(description=_('Телефон'), ordering='phone')
    def display_phone(self, obj):
        if obj.phone:
            return format_html('<span class="km-org-phone">{}</span>', obj.phone)
        return mark_safe('<span class="text-muted" style="font-size: 13px;">—</span>')

    def _dashboard_counts(self):
        from catalog.models import Place
        from catalog.services.organization_state import current_branch_q
        counts = self._organization_counts()
        stale = Place.objects.filter(organization__isnull=False, deleted_at__isnull=True,
                                     organization__archived_at__isnull=True).exclude(current_branch_q())
        counts['stale_links'] = stale.values('organization_id').distinct().count()
        return counts

    def _organization_counts(self):
        return Organization.objects.aggregate(
            total=Count('pk', distinct=True),
            published=Count('pk', filter=organization_status_filter('published'), distinct=True),
            pending=Count('pk', filter=organization_status_filter('pending'), distinct=True),
            draft=Count('pk', filter=organization_status_filter('draft'), distinct=True),
            inconsistent=Count('pk', filter=organization_status_filter('inconsistent'), distinct=True),
            with_places=Count('pk', filter=Q(places__isnull=False, places__deleted_at__isnull=True), distinct=True),
        )

    @admin.display(description=_('Публикация и изменения'))
    def publication_badge(self, obj):
        from catalog.services.organization_state import lifecycle
        if obj.archived_at:
            return format_html('<span class="km-status-badge km-status-draft">{}</span>', _('Архивная'))
        published = obj.status == 'published' and obj.approved_at
        status = 'published' if published else 'draft'
        label = _('Опубликовано') if published else _('Не опубликовано')
        badge = format_html('<span class="km-status-badge km-status-{}">{}</span>', status, label)
        revision = getattr(obj, 'content_revision', None)
        state = lifecycle(obj, revision)
        if state.code == 'inconsistent':
            badge = format_html('<span class="km-status-badge km-status-draft">{}</span> <span class="km-status-badge km-org-state--danger" title="{}">{}</span>',
                                label, state.hint, state.label)
        if revision and revision.status == 'pending':
            return format_html('{} <span class="km-status-badge km-status-pending">{}</span>', badge, _('Изменения на модерации'))
        if revision and revision.status == 'rejected':
            return format_html('{} <span class="km-status-badge km-org-state--warn">{}</span>', badge, _('Возвращено на доработку'))
        return badge

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        from catalog.models import Place
        from catalog.services import organization_state as state_service
        context = dict(extra_context or {})
        obj = self.get_object(request, object_id) if object_id else None
        if obj is None:
            context.setdefault('title', _('Новая организация'))
            context['km_org_can_publish'] = self.can_publish(request.user)
            context['km_org_preview_url'] = reverse('admin:catalog_organization_add_site_preview')
        else:
            revision = VolunteerPlaceRevision.objects.filter(organization=obj).first()
            places = list(Place.objects.filter(organization=obj, deleted_at__isnull=True).select_related('owner').order_by('pk'))
            health = state_service.branch_health(obj, places=places)
            data = dict(revision.payload) if revision and revision.status in ('draft', 'pending', 'rejected') else None
            context.update({
                'km_org_can_publish': (
                    self.can_publish(request.user) and self.has_change_permission(request, obj)
                    and getattr(revision, 'status', None) != VolunteerPlaceRevision.Status.PENDING
                ),
                'km_org_state': state_service.lifecycle(obj, revision),
                'km_org_health': health,
                'km_org_ready': state_service.readiness(obj, data=data, health=health),
                'km_org_public_url': self.view_on_site(obj),
                'km_org_preview_url': reverse('admin:catalog_organization_site_preview', args=[obj.pk]),
                'km_org_can_review': self.can_publish(request.user),
                'km_org_revision': revision,
            })
        return super().changeform_view(request, object_id, form_url, context)

    def view_on_site(self, obj):
        from catalog.services.features import is_organizations_section_enabled

        return obj.get_absolute_url() if obj.is_public and is_organizations_section_enabled() else None

    @staticmethod
    def can_publish(user):
        from catalog.services.business_team import platform_has_action
        return platform_has_action(user=user, action='place.publish')

    def save_model(self, request, obj, form, change):
        publish_now = '_save_and_publish' in request.POST and self.can_publish(request.user)
        if publish_now and change and VolunteerPlaceRevision.objects.filter(
            organization_id=obj.pk, status=VolunteerPlaceRevision.Status.PENDING,
        ).exists():
            raise ValidationError(_('Ожидает решения модератора'))
        super().save_model(request, obj, form, change)
        if not publish_now:
            status_message = _('Черновик сохранён.') if '_save_draft' in request.POST else _('Организация отправлена на проверку.')
            self.message_user(request, status_message, level=messages.SUCCESS, fail_silently=True)
            return
        # One click for staff who are allowed to publish: the candidate is
        # still created and reviewed through the same service, so history and
        # checks stay identical to the two-step path.
        revision = VolunteerPlaceRevision.objects.filter(organization_id=obj.pk, status='pending').first()
        if revision is not None:
            publication.review(actor=request.user, revision_id=revision.pk, version=revision.version, approve=True)
            obj.refresh_from_db()
            self.message_user(request, _('Организация опубликована.'), level=messages.SUCCESS, fail_silently=True)

    def _dashboard_stats(self, request, counts: dict):
        from catalog.models.catalog_structure import PublicationState
        return (
            {
                "label": _("Всего организаций"),
                "count": counts["total"],
                "url": "?",
                "tone": "info",
            },
            {
                "label": _("Опубликовано"),
                "count": counts["published"],
                "url": f"?status={PublicationState.PUBLISHED}",
                "tone": "good",
            },
            {
                "label": _("На модерации"),
                "count": counts["pending"],
                "url": f"?status={PublicationState.PENDING}",
                "tone": "warn",
            },
            {
                "label": _("Черновики"),
                "count": counts["draft"],
                "url": f"?status={PublicationState.DRAFT}",
                "tone": "muted",
            },
            *(({
                "label": _("Требуют решения"),
                "count": counts["inconsistent"],
                "url": "?status=inconsistent",
                "tone": "danger",
            },) if counts.get("inconsistent") else ()),
            {
                "label": _("С филиалами"),
                "count": counts["with_places"],
                "url": "?has_branches=yes",
                "tone": "good",
            },
        )

    def _quick_filters(self, request, counts: dict):
        from catalog.models.catalog_structure import PublicationState
        current_status = request.GET.get("status")
        current_branches = request.GET.get("has_branches")
        return [
            {
                "key": "all",
                "label": _("Все организации"),
                "count": counts["total"],
                "url": "?",
                "active": not current_status and not current_branches,
            },
            {
                "key": "published",
                "label": _("Опубликовано"),
                "count": counts["published"],
                "url": f"?status={PublicationState.PUBLISHED}",
                "active": current_status == PublicationState.PUBLISHED,
            },
            {
                "key": "pending",
                "label": _("На модерации"),
                "count": counts["pending"],
                "url": f"?status={PublicationState.PENDING}",
                "active": current_status == PublicationState.PENDING,
            },
            {
                "key": "draft",
                "label": _("Черновики"),
                "count": counts["draft"],
                "url": f"?status={PublicationState.DRAFT}",
                "active": current_status == PublicationState.DRAFT,
            },
            {
                "key": "with_branches",
                "label": _("С филиалами"),
                "count": counts["with_places"],
                "url": "?has_branches=yes",
                "active": current_branches == "yes",
            },
            *(({
                "key": "inconsistent",
                "label": _("Требуют решения"),
                "count": counts.get("inconsistent", 0),
                "url": "?status=inconsistent",
                "active": current_status == "inconsistent",
            },) if counts.get("inconsistent") or current_status == "inconsistent" else ()),
            *(({
                "key": "stale",
                "label": _("Неактуальные связи"),
                "count": counts.get("stale_links", 0),
                "url": "?has_branches=stale",
                "active": current_branches == "stale",
            },) if counts.get("stale_links") or current_branches == "stale" else ()),
        ]

    def _bulk_actions(self):
        return (
            {"name": "mark_published", "label": _("Опубликовать"), "tone": "good", "icon": "fas fa-bullhorn", "description": _("Опубликовать выбранные организации.")},
            {"name": "mark_draft", "label": _("В черновик"), "tone": "muted", "icon": "far fa-file-alt", "description": _("Снять выбранные организации с публикации.")},
        )

    def get_ordering(self, request):
        sort_val = request.GET.get("sort") or "updated_desc"
        if sort_val == "created_desc":
            return ["-created_at"]
        elif sort_val == "created_asc":
            return ["created_at"]
        elif sort_val == "updated_asc":
            return ["updated_at"]
        elif sort_val == "name_asc":
            return ["name_ru", "name_az", "name_en"]
        elif sort_val == "name_desc":
            return ["-name_ru", "-name_az", "-name_en"]
        return ["-updated_at"]

    def changelist_view(self, request, extra_context=None):
        counts = self._dashboard_counts()
        quick_filters = self._quick_filters(request, counts=counts)
        sort_labels = {
            "created_desc": _("Создано (новые)"),
            "created_asc": _("Создано (старые)"),
            "updated_desc": _("Обновлено (новые)"),
            "updated_asc": _("Обновлено (старые)"),
            "name_asc": _("По названию (А → Я)"),
            "name_desc": _("По названию (Я → А)"),
        }
        km_current_sort = request.GET.get("sort") or "updated_desc"
        km_current_sort_label = sort_labels.get(km_current_sort, sort_labels["updated_desc"])

        extra_context = {
            "organization_dashboard_stats": self._dashboard_stats(request, counts=counts),
            "km_primary_quick_filters": quick_filters,
            "km_secondary_quick_filters": [],
            "km_current_sort": km_current_sort,
            "km_current_sort_label": km_current_sort_label,
            "organization_bulk_actions": self._bulk_actions(),
            "km_org_counts": counts,
            "km_search_label": _("Поиск организаций"),
            "km_search_placeholder": _("Название AZ/RU/EN, адрес, телефон, владелец"),
            "km_changelist_reset_url": "?",
            "km_suggestions_url": reverse("admin:catalog_organization_search_suggestions"),
            **(extra_context or {}),
        }
        return super().changelist_view(request, extra_context=extra_context)

    def _bulk_transition(self, request, queryset, *, publish):
        succeeded = skipped = 0
        failures = []
        for obj in queryset:
            try:
                if not self.has_change_permission(request):
                    raise PermissionDenied
                if publish:
                    revision = VolunteerPlaceRevision.objects.filter(organization=obj, status='pending').first()
                    if revision is None:
                        raise ValidationError(_('Сначала отправьте сведения на проверку.'))
                    publication.review(actor=request.user, revision_id=revision.pk, version=revision.version, approve=True)
                else:
                    publication.unpublish(actor=request.user, target_type='organization', target_id=obj.pk,
                        expected_version=obj.content_version)
                succeeded += 1
            except PermissionDenied:
                skipped += 1
                failures.append(_('Организация #%(id)s: нет прав для этого действия.') % {'id': obj.pk})
            except ValidationError as exc:
                skipped += 1
                reason = (_('Сначала отправьте сведения на проверку.') if publish and not
                    VolunteerPlaceRevision.objects.filter(organization=obj, status='pending').exists()
                    else _('Данные изменились или переход недоступен. Откройте карточку и проверьте заявку.'))
                failures.append(_('Организация #%(id)s: %(reason)s') % {'id': obj.pk, 'reason': reason})
        self.message_user(request,
            _('Выполнено: %(done)s. Пропущено: %(skipped)s. Для публикации нужны ожидающая заявка и права модерации; для снятия — отсутствие незавершённых изменений.')
            % {'done': succeeded, 'skipped': skipped},
            level=messages.WARNING if skipped else messages.SUCCESS)
        for failure in failures[:5]:
            self.message_user(request, failure, level=messages.WARNING)

    @admin.action(description=_("Опубликовать выбранные организации"))
    def mark_published(self, request, queryset):
        self._bulk_transition(request, queryset, publish=True)

    @admin.action(description=_("Перевести выбранные организации в черновики"))
    def mark_draft(self, request, queryset):
        self._bulk_transition(request, queryset, publish=False)

    def create_target(self, request, data):
        from catalog.services.organization_ownership import create_organization
        values = {name: data[name] for name in ('name_az', 'name_ru', 'name_en', 'description_az', 'description_ru', 'description_en', 'phone', 'whatsapp', 'website') if name in data}
        return create_organization(actor=request.user, values=values)

    def related_links(self, obj):
        return [(_('Филиалы'), reverse('admin:catalog_place_changelist') + f'?organization__id__exact={obj.pk}'),
                (_('Программы'), reverse('admin:catalog_program_changelist') + f'?organization__id__exact={obj.pk}'),
                (_('Сотрудники'), reverse('admin:catalog_organizationgrant_changelist') + f'?organization__id__exact={obj.pk}')]


@admin.register(Program)
class ProgramAdmin(BusinessEditor):
    editor_sections = (( _('Организация и рубрика'), ('organization', 'category', 'subcategory')), (_('Названия'), ('name_az', 'name_ru', 'name_en')), (_('Описание'), ('description_az', 'description_ru', 'description_en')))
    form = ProgramForm
    list_display = ('display_name', 'organization_link', 'category', 'publication_badge', 'activities_count_badge', 'display_updated_at')
    list_filter = (PublicationStatusFilter, OrganizationFilter, CategoryFilter)
    search_fields = ('name_az', 'name_ru', 'name_en', 'organization__name_az', 'organization__name_ru')
    structural_fields = frozenset({'organization'})

    @admin.display(description=_('Организация'))
    def organization_link(self, obj):
        if not obj.organization_id:
            return '—'
        url = reverse('admin:catalog_organization_change', args=[obj.organization_id])
        name = obj.organization.name_ru or obj.organization.name_az or obj.organization.name_en or f'#{obj.organization_id}'
        return format_html('<a href="{}" style="font-weight: 500;"><i class="fas fa-building mr-1 text-muted"></i>{}</a>', url, name)

    @admin.display(description=_('Занятия'))
    def activities_count_badge(self, obj):
        count = obj.activities.filter(archived_at__isnull=True).count()
        url = reverse('admin:catalog_activity_changelist') + f'?program__id__exact={obj.pk}'
        if count > 0:
            return format_html('<a href="{}" class="badge badge-info" style="font-size: 13px; font-weight: 500; padding: 4px 8px;"><i class="fas fa-chalkboard-teacher mr-1"></i> {}</a>', url, count)
        return mark_safe('<span class="text-muted" style="font-size: 13px;">—</span>')

    def create_target(self, request, data):
        obj = Program(organization=data['organization'], created_by=request.user)
        obj.save()
        return obj


@admin.register(Activity)
class ActivityAdmin(BusinessEditor):
    editor_sections = (( _('Место и программа'), ('place', 'program', 'category', 'subcategory')), (_('Названия'), ('name_az', 'name_ru', 'name_en')), (_('Описание'), ('description_az', 'description_ru', 'description_en')), (_('Условия занятия'), ('supplement_az', 'supplement_ru', 'supplement_en')))
    form = ActivityForm
    list_display = ('display_name', 'place_link', 'program_link', 'publication_badge', 'groups_count_badge', 'display_updated_at')
    list_filter = (PublicationStatusFilter, PlaceFilter)
    search_fields = ('name_az', 'name_ru', 'name_en', 'place__name_az', 'place__name_ru', 'program__name_az', 'program__name_ru')
    structural_fields = frozenset({'place', 'program'})

    @admin.display(description=_('Место / Филиал'))
    def place_link(self, obj):
        if not obj.place_id:
            return '—'
        url = reverse('admin:catalog_place_change', args=[obj.place_id])
        name = obj.place.name_ru or obj.place.name_az or f'#{obj.place_id}'
        return format_html('<a href="{}" style="font-weight: 500;"><i class="fas fa-map-marker-alt mr-1 text-muted"></i>{}</a>', url, name)

    @admin.display(description=_('Программа'))
    def program_link(self, obj):
        if not obj.program_id:
            return format_html('<span class="text-muted">{}</span>', _('Индивидуальная'))
        url = reverse('admin:catalog_program_change', args=[obj.program_id])
        name = obj.program.name_ru or obj.program.name_az or obj.program.name_en or f'#{obj.program_id}'
        return format_html('<a href="{}" style="font-weight: 500;"><i class="fas fa-book-open mr-1 text-muted"></i>{}</a>', url, name)

    @admin.display(description=_('Группы / Тарифы'))
    def groups_count_badge(self, obj):
        count = obj.offering_groups.filter(archived_at__isnull=True).count()
        url = reverse('admin:catalog_offeringgroup_changelist') + f'?activity__id__exact={obj.pk}'
        if count > 0:
            return format_html('<a href="{}" class="badge badge-success" style="font-size: 13px; font-weight: 500; padding: 4px 8px;"><i class="fas fa-users mr-1"></i> {}</a>', url, count)
        return mark_safe('<span class="text-muted" style="font-size: 13px;">—</span>')

    def create_target(self, request, data):
        obj = Activity(place=data['place'], program=data.get('program'))
        obj.save()
        return obj

    def related_links(self, obj):
        return [(_('Группы и тарифы'), reverse('admin:catalog_offeringgroup_changelist') + f'?activity__id__exact={obj.pk}'),
                (_('Тарифы места'), reverse('admin:catalog_place_change', args=[obj.place_id]) + '#pricing')]


@admin.register(OfferingGroup)
class OfferingGroupAdmin(BusinessEditor):
    editor_sections = (( _('Занятие'), ('activity',)), (_('Группа'), ('name_az', 'name_ru', 'name_en', 'age_from', 'age_to', 'lesson_format', 'language')), (_('Расписание и преподаватели'), ('schedule_text', 'teachers_text')), (_('Условия занятий'), ('conditions_az', 'conditions_ru', 'conditions_en')))
    form = OfferingGroupForm
    structural_fields = frozenset({'activity'})
    list_display = ('display_name', 'activity_link', 'age_display', 'format_display', 'language', 'display_updated_at')
    list_filter = (LessonFormatFilter,)
    search_fields = ('name_az', 'name_ru', 'name_en', 'activity__name_az', 'activity__name_ru')

    @admin.display(description=_('Занятие'))
    def activity_link(self, obj):
        if not obj.activity_id:
            return '—'
        url = reverse('admin:catalog_activity_change', args=[obj.activity_id])
        name = obj.activity.name_ru or obj.activity.name_az or f'#{obj.activity_id}'
        return format_html('<a href="{}" style="font-weight: 500;">{}</a>', url, name)

    @admin.display(description=_('Возраст'))
    def age_display(self, obj):
        if obj.age_from is not None and obj.age_to is not None:
            return f'{obj.age_from}–{obj.age_to} лет'
        elif obj.age_from is not None:
            return f'от {obj.age_from} лет'
        elif obj.age_to is not None:
            return f'до {obj.age_to} лет'
        return '—'

    @admin.display(description=_('Формат'))
    def format_display(self, obj):
        return obj.get_lesson_format_display() if obj.lesson_format else '—'

    def create_target(self, request, data):
        obj = OfferingGroup(activity=data['activity'])
        obj.save()
        return obj

    def related_links(self, obj):
        return [(_('Тарифы группы'), reverse('admin:catalog_place_change', args=[obj.activity.place_id]) + '#pricing')]
