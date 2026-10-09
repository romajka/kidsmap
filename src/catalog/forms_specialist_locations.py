"""Shared aggregate check over validated practice rows; no inferred affiliation."""
from django.forms.models import BaseInlineFormSet
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from catalog.models import Specialist

class BasePracticeLocationFormSet(BaseInlineFormSet):
    require_active = True
    def _construct_form(self,index,**kwargs):
        form=super()._construct_form(index,**kwargs)
        # BaseInlineFormSet sets only the FK value. Model clean needs the
        # unsaved parent too when adding a profile/proposal with practice rows.
        form.instance.specialist=self.instance
        return form

    def clean(self):
        super().clean()
        if any(self.errors):return
        if self.require_active and self.instance.consultation_format in (Specialist.FORMAT_OFFLINE,Specialist.FORMAT_BOTH):
            if not any(form.cleaned_data.get('is_active') and not form.cleaned_data.get('DELETE') and
                       (form.cleaned_data.get('place') or form.cleaned_data.get('address')) for form in self.forms):
                raise ValidationError(_('Для очного формата работы (или онлайн и очно) необходимо указать хотя бы одно активное место приема.'))

from django import forms
from django.forms.models import inlineformset_factory
from django.db.models import Q
from catalog.models import Place,SpecialistPracticeLocation
from catalog.services import specialist_domain,business_team
from catalog.services.content_quality import public_place_queryset


def visible_practice_places(actor):
    public=public_place_queryset(Place.objects.all()).values('pk')
    own=business_team.accessible_place_ids(user=actor,action='place.view')
    return Place.objects.filter(Q(pk__in=public)|Q(pk__in=own),deleted_at__isnull=True).distinct()


class PracticePlaceChoice(forms.ModelChoiceField):
    def label_from_instance(self,obj):
        return obj.name_i18n() if obj.pk in self.visible_ids else _('Карточка недоступна')+f' #{obj.pk}'


class PracticeLocationForm(forms.ModelForm):
    place=PracticePlaceChoice(queryset=Place.objects.none(),required=False,label=_('Место KidsMap'))
    class Meta:
        model=SpecialistPracticeLocation
        fields=('place','address','region','district','metro','lat','lng','schedule','price_per_session','phone','is_primary','is_active')
        widgets={'schedule':forms.Textarea(attrs={'rows':2}),'phone':forms.TextInput(attrs={'inputmode':'tel'}),'price_per_session':forms.NumberInput(attrs={'min':0}),'lat':forms.NumberInput(attrs={'step':'any'}),'lng':forms.NumberInput(attrs={'step':'any'})}

    def __init__(self,*args,actor,allow_incomplete=False,**kwargs):
        super().__init__(*args,**kwargs)
        self.allow_incomplete=allow_incomplete
        self.existing_place_id=self.instance.place_id if self.instance.pk else None
        visible=visible_practice_places(actor)
        self.fields['place'].visible_ids=set(visible.values_list('pk',flat=True))
        self.fields['place'].queryset=Place.objects.filter(Q(pk__in=visible.values('pk'))|Q(pk=self.existing_place_id))
        for field in self.fields.values():field.widget.attrs.setdefault('class','field')

    def _post_clean(self):
        # Working drafts have always allowed incomplete offline details. Keep
        # type/FK/field validation, defer the model's offline completeness rule.
        if not self.allow_incomplete:return super()._post_clean()
        from copy import copy
        parent=self.instance.specialist
        draft_parent=copy(parent);draft_parent.consultation_format=Specialist.FORMAT_ONLINE
        self.instance.specialist=draft_parent
        try:super()._post_clean()
        finally:self.instance.specialist=parent


class PersonPracticeLocationFormSet(BasePracticeLocationFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):return
        existing=set(self.get_queryset().values_list('pk',flat=True))
        primaries=0
        for form in self.forms:
            row=form.cleaned_data
            if row.get('id') and row['id'].pk not in existing:
                form.add_error('id',_('Место приёма не принадлежит этому профилю.'))
            if row.get('is_primary') and not row.get('DELETE'):primaries+=1
        if primaries>1:raise ValidationError(_('Выберите только одно основное место приёма.'))


def practice_location_formset(*,actor,specialist,data=None,require_active=True):
    actor=specialist_domain.require_actor(actor)
    if specialist.pk:specialist_domain.require_person(actor,specialist)
    factory=inlineformset_factory(Specialist,SpecialistPracticeLocation,form=PracticeLocationForm,
        formset=PersonPracticeLocationFormSet,extra=1,can_delete=True,max_num=30,validate_max=True,absolute_max=31)
    result=factory(data,instance=specialist,prefix='locations',form_kwargs={'actor':actor,'allow_incomplete':not require_active})
    result.require_active=require_active
    return result


def save_practice_locations(*,specialist,formset):
    """Called only under the parent lock/transaction by the verified-person save."""
    current={row.pk:row for row in SpecialistPracticeLocation.objects.select_for_update().filter(specialist=specialist)}
    identity=('place_id','address','region_id','district_id','metro_id','lat','lng')
    fields=PracticeLocationForm.Meta.fields
    for form in formset.forms:
        row=form.cleaned_data
        if not row:continue
        previous=current.get(row['id'].pk) if row.get('id') else None
        if row.get('id') and previous is None:raise ValidationError(_('Место приёма не принадлежит этому профилю.'))
        if row.get('DELETE'):
            if previous:
                previous.is_active=False;previous.is_primary=False;previous.save(update_fields=['is_active','is_primary'])
            continue
        values={name:row.get(name) for name in fields}
        if previous and any(getattr(previous,name)!=getattr(form.instance,name) for name in identity):
            previous.is_active=False;previous.is_primary=False;previous.save(update_fields=['is_active','is_primary'])
            previous=None
        target=previous or SpecialistPracticeLocation(specialist=specialist)
        for name,value in values.items():setattr(target,name,value)
        target.save()
    if specialist.consultation_format==Specialist.FORMAT_ONLINE:
        specialist.practice_locations.filter(is_active=True).update(is_active=False)
