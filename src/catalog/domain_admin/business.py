"""Admin editors for the additive business hierarchy.

Content is proposed through publication; structure is created through its
locked model services. Review and visibility are explicit POST actions.
"""
from operator import mod

from django import forms
from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import HttpResponseRedirect
from django.urls import path, reverse
from django.db.models import Count, Q
from django.utils.functional import lazy
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from catalog.models import Activity, OfferingGroup, Organization, Program, VolunteerPlaceRevision
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
    class Meta:
        model = Organization
        fields = ('name_az', 'name_ru', 'name_en', 'description_az', 'description_ru', 'description_en', 'phone', 'whatsapp', 'website')
        labels = {**{f'name_{lang}':_format_label(_('Название организации (%(language)s)'), {'language':lang.upper()}) for lang in ('az','ru','en')},
            **{f'description_{lang}':_format_label(_('Описание организации (%(language)s)'), {'language':lang.upper()}) for lang in ('az','ru','en')},
            'phone':_('Общий телефон организации'),'whatsapp':_('Общий WhatsApp организации'),'website':_('Сайт организации')}
        help_texts = {'phone':_('Используется в филиале, если там не указан собственный телефон.'),
            'website':_('Используется в филиале, если там не указан собственный сайт.')}


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


class OrganizationHasBranchesFilter(admin.SimpleListFilter):
    title = _('Филиалы')
    parameter_name = 'has_branches'

    def lookups(self, request, model_admin):
        return (
            ('yes', _('Есть филиалы')),
            ('no', _('Без филиалов')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(places__isnull=False, places__deleted_at__isnull=True).distinct()
        if self.value() == 'no':
            return queryset.filter(Q(places__isnull=True) | Q(places__deleted_at__isnull=False)).distinct()
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
    readonly_fields = ('publication_badge', 'ownership_badge', 'verified_badge', 'content_version', 'archived_at')
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
        return ['publication_badge', 'ownership_badge', 'verified_badge', *fields, 'source_version', 'candidate_version', 'content_version', 'archived_at'] if obj else [*fields, 'source_version', 'candidate_version']

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
        versions = tuple(name for name in ('source_version', 'candidate_version', 'content_version', 'archived_at') if name in available)
        available.difference_update(versions)
        if available:
            sections.append((None, {'fields': tuple(sorted(available))}))
        if versions:
            sections.append((None, {'fields': versions, 'classes': ('collapse',)}))
        return sections

    def get_urls(self):
        base = super().get_urls()
        name = f'{self.opts.app_label}_{self.opts.model_name}'
        extra = [path('<path:object_id>/transition/', self.admin_site.admin_view(self.transition_view), name=f'{name}_transition')]
        return extra + base

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        context = dict(extra_context or {})
        obj = self.get_object(request, object_id) if object_id else None
        context['km_business_kind'] = self.publication_kind
        context['km_business_object'] = obj
        if obj:
            context['km_business_revision'] = VolunteerPlaceRevision.objects.filter(**{self.publication_kind: obj}).first()
            revision = context['km_business_revision']
            if revision and revision.status in {'draft', 'pending', 'rejected'}:
                current = publication.snapshot(obj, self.publication_kind)
                context['km_business_changes'] = [
                    {'label': obj._meta.get_field(name).verbose_name,
                     'current': current.get(name), 'candidate': revision.payload[name]}
                    for name in revision.changed_fields
                    if name in revision.payload and name in self.form._meta.fields
                ]
            context['km_business_transition_url'] = reverse(f'admin:{self.opts.app_label}_{self.opts.model_name}_transition', args=[obj.pk])
            from .navigation import business_navigation
            context['km_business_links'] = business_navigation(request, obj)
            context['km_business_can_add_group'] = any('offeringgroup/add/' in url for _label, url in context['km_business_links'])
            context['km_business_can_invite'] = isinstance(obj, Organization) and obj.owner_id == request.user.pk
            if isinstance(obj, Activity):
                context['km_activity_groups'] = list(obj.offering_groups.filter(archived_at__isnull=True).order_by('pk'))
        try:
            return super().changeform_view(request, object_id, form_url, context)
        except ValidationError as exc:
            self.message_user(request, '; '.join(exc.messages), level=messages.ERROR)
            return HttpResponseRedirect(request.path)

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
    editor_sections = (( _('Названия'), ('name_az', 'name_ru', 'name_en')), (_('Описание'), ('description_az', 'description_ru', 'description_en')), (_('Контакты'), ('phone', 'whatsapp', 'website')))
    form = OrganizationForm
    structural_fields = frozenset()
    list_display = ('display_name', 'publication_badge', 'ownership_badge', 'places_count_badge', 'programs_count_badge', 'display_phone', 'display_updated_at')
    list_filter = (PublicationStatusFilter, OrganizationHasBranchesFilter)
    search_fields = ('name_az', 'name_ru', 'name_en', 'phone', 'website')
    actions = ['mark_published', 'mark_draft']

    @admin.display(description=_('Филиалы'))
    def places_count_badge(self, obj):
        count = obj.places.filter(deleted_at__isnull=True).count()
        url = reverse('admin:catalog_place_changelist') + f'?organization__id__exact={obj.pk}'
        if count > 0:
            return format_html('<a href="{}" class="km-org-count-badge km-org-count-badge--branches" title="{}"><svg class="km-i" viewBox="0 0 960 960" aria-hidden="true"><use href="#kmi-place"></use></svg>{}</a>', url, _('Смотреть филиалы'), count)
        return mark_safe('<span class="text-muted" style="font-size: 13px;">—</span>')

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
        from catalog.models.catalog_structure import PublicationState
        qs = Organization.objects.all()
        return qs.aggregate(
            total=Count("id"),
            published=Count("id", filter=Q(status=PublicationState.PUBLISHED)),
            pending=Count("id", filter=Q(status=PublicationState.PENDING)),
            draft=Count("id", filter=Q(status=PublicationState.DRAFT)),
            with_places=Count("id", filter=Q(places__isnull=False, places__deleted_at__isnull=True), distinct=True),
        )

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
            "km_search_label": _("Поиск организаций"),
            "km_search_placeholder": _("Название, телефон, сайт..."),
            "km_changelist_reset_url": "?",
            "km_disable_search_suggestions": True,
            **(extra_context or {}),
        }
        return super().changelist_view(request, extra_context=extra_context)

    @admin.action(description=_("Опубликовать выбранные организации"))
    def mark_published(self, request, queryset):
        from catalog.models.catalog_structure import PublicationState
        count = 0
        for obj in queryset:
            if obj.status != PublicationState.PUBLISHED:
                obj.status = PublicationState.PUBLISHED
                obj.save(update_fields=['status', 'updated_at'])
                count += 1
        self.message_user(request, _(f"Опубликовано организаций: {count}"), level=messages.SUCCESS)

    @admin.action(description=_("Перевести выбранные организации в черновики"))
    def mark_draft(self, request, queryset):
        from catalog.models.catalog_structure import PublicationState
        count = 0
        for obj in queryset:
            if obj.status != PublicationState.DRAFT:
                obj.status = PublicationState.DRAFT
                obj.save(update_fields=['status', 'updated_at'])
                count += 1
        self.message_user(request, _(f"Переведено в черновики организаций: {count}"), level=messages.SUCCESS)

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
