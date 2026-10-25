"""Small, validated public contact links shared by all Place entry points."""
from urllib.parse import urlsplit
from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from catalog.services.permanent_place_rules import copy as t


def normalize_public_links(value):
    if value is None or value == '':return []
    if not isinstance(value,list) or len(value)>5:
        raise ValidationError(t('Добавьте не больше 5 ссылок.','Ən çox 5 keçid əlavə edin.','Add up to 5 links.'))
    result=[]
    for row in value:
        if not isinstance(row,dict) or set(row)!={'label','url'}:raise ValidationError(t('Для ссылки нужны название и адрес.','Keçid üçün ad və ünvan lazımdır.','Each link needs a name and address.'))
        label,url=row['label'],row['url']
        if not isinstance(label,str) or not isinstance(url,str):raise ValidationError('Invalid public link.')
        label,url=label.strip(),url.strip()
        if not label or len(label)>80 or len(url)>500 or any(ord(c)<32 for c in label+url):raise ValidationError(t('Название ссылки — от 1 до 80 символов, адрес — до 500.','Keçidin adı 1–80, ünvanı 500 simvoladək olmalıdır.','Use a link name of 1–80 characters and a URL of up to 500.'))
        try:
            parts=urlsplit(url)
            if parts.username or parts.password:raise ValueError
            URLValidator(schemes=['http','https'])(url)
        except (ValueError,ValidationError):raise ValidationError(t('Укажите публичную ссылку с https:// или http://, без логина и пароля.','https:// və ya http:// ilə başlayan, giriş məlumatı olmayan açıq keçid göstərin.','Enter a public http:// or https:// link without login credentials.'))
        result.append({'label':label,'url':url})
    return result


def validate_public_links(value):
    normalize_public_links(value)


class PublicLinksFormMixin:
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        if 'public_links' in self.fields:
            self.fields['public_links'].widget=forms.HiddenInput(attrs={'data-public-links-input':''})
            self.fields['public_links'].required=False

    def clean_public_links(self):
        if self.is_bound and 'public_links' not in self.data:
            return normalize_public_links(self.initial.get('public_links',getattr(self.instance,'public_links',[])))
        return normalize_public_links(self.cleaned_data.get('public_links'))
