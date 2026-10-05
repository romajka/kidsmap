"""Admin editors for the additive business hierarchy.

Content is proposed through publication; structure is created through its
locked model services. Review and visibility are explicit POST actions.
"""
from django import forms
from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import HttpResponseRedirect
from django.urls import path, reverse
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


class OrganizationForm(CandidateForm):
    class Meta:
        model = Organization
        fields = ('name_az', 'name_ru', 'name_en', 'description_az', 'description_ru', 'description_en', 'phone', 'whatsapp', 'website')


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


class BusinessEditor(admin.ModelAdmin):
    change_form_template = 'admin/catalog/business/change_form.html'
    actions = None
    @property
    def publication_kind(self):
        return 'offering_group' if self.opts.model_name == 'offeringgroup' else self.opts.model_name
    readonly_fields = ('publication_badge', 'ownership_badge', 'verified_badge', 'content_version', 'archived_at')
    list_display = ('display_name', 'publication_badge', 'content_version', 'updated_at')
    search_fields = ('name_az', 'name_ru', 'name_en')
    list_filter = ('status',)
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
            return _('Публикация занятия: %(status)s') % {'status': obj.activity.get_status_display()}
        return obj.get_status_display()

    @admin.display(description=_('Владение'))
    def ownership_badge(self, obj):
        target = obj if isinstance(obj, Organization) else (obj.organization if isinstance(obj, Program) else (obj.activity.place if isinstance(obj, OfferingGroup) else obj.place))
        return _('Владелец назначен') if target.owner_id else _('Владелец не назначен')

    @admin.display(description=_('Проверка данных'))
    def verified_badge(self, obj):
        if isinstance(obj, Organization):
            return _('Владение проверено') if obj.ownership_verified_at else _('Владение не проверено')
        if isinstance(obj, OfferingGroup):
            return _('Условия подтверждены') if obj.conditions_verified_at else _('Условия не подтверждены')
        return _('Отдельный статус проверки не установлен')

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
            context['km_business_links'] = self.related_links(obj)
            context['km_business_can_invite'] = isinstance(obj, Organization) and obj.owner_id == request.user.pk
            if isinstance(obj, Activity):
                context['km_activity_groups'] = list(obj.offering_groups.filter(archived_at__isnull=True).order_by('pk'))
        try:
            return super().changeform_view(request, object_id, form_url, context)
        except ValidationError as exc:
            self.message_user(request, '; '.join(exc.messages), level=messages.ERROR)
            return HttpResponseRedirect(request.path)

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
    editor_sections = (( _('Названия'), ('name_az', 'name_ru', 'name_en')), (_('Описание'), ('description_az', 'description_ru', 'description_en')), (_('Контакты'), ('phone', 'whatsapp', 'website')))
    form = OrganizationForm
    structural_fields = frozenset()

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
    list_filter = ('status', 'organization')
    structural_fields = frozenset({'organization'})

    def create_target(self, request, data):
        obj = Program(organization=data['organization'], created_by=request.user)
        obj.save()
        return obj


@admin.register(Activity)
class ActivityAdmin(BusinessEditor):
    editor_sections = (( _('Место и программа'), ('place', 'program', 'category', 'subcategory')), (_('Названия'), ('name_az', 'name_ru', 'name_en')), (_('Описание'), ('description_az', 'description_ru', 'description_en')), (_('Условия занятия'), ('supplement_az', 'supplement_ru', 'supplement_en')))
    form = ActivityForm
    list_filter = ('status', 'place')
    structural_fields = frozenset({'place', 'program'})

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
    list_filter = ('activity',)

    def create_target(self, request, data):
        obj = OfferingGroup(activity=data['activity'])
        obj.save()
        return obj

    def related_links(self, obj):
        return [(_('Тарифы группы'), reverse('admin:catalog_place_change', args=[obj.activity.place_id]) + '#pricing')]
