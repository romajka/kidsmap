import os
from xml.etree import ElementTree

from django.conf import settings
from django.contrib import admin
from django.core.files.storage import FileSystemStorage
from django.db.models import Count, Prefetch, Q
from django import forms
from django.http import JsonResponse
from django.urls import path
from django.template.response import TemplateResponse
from django.utils.translation import gettext_lazy as _
from PIL import Image, UnidentifiedImageError

from catalog.models import Category, Subcategory


ICON_EXTENSIONS = {".svg", ".png", ".webp"}
ICON_MAX_FILE_SIZE = 500 * 1024
ICON_RASTER_SIZE = 512
ICON_HELP_TEXT = _("SVG с квадратным viewBox или PNG/WebP 512×512 px, до 500 КБ.")


def validate_icon_upload(uploaded_file):
    """Validate icon files consistently for categories and subcategories."""
    if uploaded_file.size > ICON_MAX_FILE_SIZE:
        raise forms.ValidationError(_("Иконка весит больше 500 КБ. Сожмите файл и загрузите снова."))

    extension = os.path.splitext(uploaded_file.name)[1].lower()
    if extension not in ICON_EXTENSIONS:
        raise forms.ValidationError(_("Подходит только SVG, PNG или WebP."))

    try:
        if extension == ".svg":
            source = uploaded_file.read()
            root = ElementTree.fromstring(source)
            if root.tag.rsplit("}", 1)[-1] != "svg":
                raise ValueError
            view_box = root.attrib.get("viewBox", "").replace(",", " ").split()
            if len(view_box) != 4 or float(view_box[2]) != float(view_box[3]) or float(view_box[2]) <= 0:
                raise forms.ValidationError(_("У SVG должен быть квадратный viewBox, например 0 0 24 24."))
            source_lower = source.lower()
            if b"<script" in source_lower or b"onload=" in source_lower or b"onerror=" in source_lower:
                raise forms.ValidationError(_("SVG не должен содержать скрипты."))
        else:
            image = Image.open(uploaded_file)
            image.verify()
            uploaded_file.seek(0)
            image = Image.open(uploaded_file)
            if image.format not in {"PNG", "WEBP"}:
                raise forms.ValidationError(_("Файл не соответствует формату PNG или WebP."))
            if image.size != (ICON_RASTER_SIZE, ICON_RASTER_SIZE):
                raise forms.ValidationError(_("PNG и WebP должны быть ровно 512×512 px."))
    except forms.ValidationError:
        raise
    except (ElementTree.ParseError, ValueError, UnidentifiedImageError, OSError):
        raise forms.ValidationError(_("Не удалось прочитать иконку. Загрузите корректный SVG, PNG или WebP."))
    finally:
        uploaded_file.seek(0)

    return uploaded_file


def save_uploaded_category_icon(uploaded_file, category_code="category-icon", folder="cat_icons"):
    ext = (uploaded_file.name.rsplit(".", 1)[-1] if "." in uploaded_file.name else "").lower()
    validate_icon_upload(uploaded_file)

    storage = FileSystemStorage(location=settings.MEDIA_ROOT, base_url=settings.MEDIA_URL)
    safe_code = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "-" for ch in (category_code or "category-icon")).strip("-")
    safe_code = safe_code or "category-icon"
    filename = storage.get_available_name(f"{folder}/{safe_code}.{ext}")
    saved_name = storage.save(filename, uploaded_file)
    return storage.url(saved_name)


class CategoryAdminForm(forms.ModelForm):
    name = forms.CharField(widget=forms.HiddenInput(), required=False)
    name_az = forms.CharField(label=_("Название (AZ)"), required=True)
    icon_upload = forms.FileField(
        label=_("Файл иконки"),
        required=False,
        help_text=ICON_HELP_TEXT,
    )

    class Meta:
        model = Category
        fields = "__all__"
        widgets = {
            "code": forms.TextInput(attrs={"autocomplete": "off", "placeholder": _("Например: education")}),
            "order": forms.NumberInput(attrs={"min": 0, "step": 1, "inputmode": "numeric"}),
            "name_ru": forms.TextInput(attrs={"placeholder": _("Например: Образование")}),
            "name_en": forms.TextInput(attrs={"placeholder": _("Например: Education")}),
            "icon": forms.TextInput(attrs={"autocomplete": "off", "placeholder": _("Например: icons/categories/sports.svg")}),
            "color_bg": forms.TextInput(attrs={"type": "color"}),
            "color_text": forms.TextInput(attrs={"type": "color"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        name_az = cleaned_data.get("name_az")
        if name_az:
            cleaned_data["name"] = name_az
        return cleaned_data

    def clean_icon_upload(self):
        uploaded_file = self.cleaned_data.get("icon_upload")
        if not uploaded_file:
            return uploaded_file
        return validate_icon_upload(uploaded_file)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["name_az"].widget.attrs.setdefault("placeholder", _("Например: Təhsil"))
        self.fields["icon"].label = _("Путь или CSS-класс")
        self.fields["icon"].help_text = _(
            "Можно указать относительный путь к иконке или CSS-класс. Например: icons/categories/sports.svg или fas fa-futbol."
        )
        self.fields["icon_upload"].widget.attrs.update({"accept": ".svg,.png,.webp", "data-km-icon-upload": "true"})

    def save(self, commit=True):
        instance = super().save(commit=False)
        uploaded_file = self.cleaned_data.get("icon_upload")
        if uploaded_file:
            instance.icon = save_uploaded_category_icon(uploaded_file, self.cleaned_data.get("code") or instance.code)
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class SubcategoryAdminForm(forms.ModelForm):
    icon_upload = forms.FileField(label=_("Файл иконки"), required=False, help_text=ICON_HELP_TEXT)

    class Meta:
        model = Subcategory
        fields = "__all__"
        widgets = {
            "icon": forms.TextInput(attrs={"autocomplete": "off", "placeholder": _("Загружается автоматически")}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["icon_upload"].widget.attrs.update({"accept": ".svg,.png,.webp", "data-km-icon-upload": "true"})
        self.fields["icon"].label = _("Путь к иконке")
        self.fields["icon"].help_text = _("Обычно заполняется после загрузки файла выше.")

    def clean_icon_upload(self):
        uploaded_file = self.cleaned_data.get("icon_upload")
        return validate_icon_upload(uploaded_file) if uploaded_file else uploaded_file

    def save(self, commit=True):
        instance = super().save(commit=False)
        uploaded_file = self.cleaned_data.get("icon_upload")
        if uploaded_file:
            instance.icon = save_uploaded_category_icon(
                uploaded_file,
                instance.code or instance.name_ru or "subcategory-icon",
                folder="subcategory_icons",
            )
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class SubcategoryInline(admin.TabularInline):
    model = Subcategory
    form = SubcategoryAdminForm
    extra = 1
    fields = ("name_ru", "name_az", "name_en", "icon_upload", "icon", "order")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    form = CategoryAdminForm
    change_form_template = "admin/catalog/category/change_form.html"
    list_display = ("code", "name_ru", "name_az", "name_en")
    search_fields = ("code", "name_ru", "name_az", "name_en")
    ordering = ("name_ru",)
    inlines = [SubcategoryInline]

    fieldsets = (
        (None, {
            "fields": (
                ("code", "name_az"),
                ("name_ru", "name_en"),
                "icon",
                ("color_bg", "color_text"),
                "name",
            )
        }),
    )

    def get_inlines(self, request, obj=None):
        if not obj or request.GET.get("_popup"):
            return []
        return self.inlines

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('upload-icon/', self.admin_site.admin_view(self.upload_icon_view), name='catalog_category_upload_icon'),
            path('toggle-active/', self.admin_site.admin_view(self.toggle_active_view), name='catalog_taxonomy_toggle_active'),
        ]
        return custom_urls + urls

    def toggle_active_view(self, request):
        from django.http import JsonResponse
        from catalog.models.category import Category, Subcategory
        
        if request.method != "POST":
            return JsonResponse({"error": "POST required"}, status=405)
            
        if not self.has_change_permission(request):
            return JsonResponse({"error": "Permission denied"}, status=403)
            
        obj_type = request.POST.get('obj_type')
        obj_id = request.POST.get('obj_id')
        
        if obj_type == 'category':
            obj = Category.objects.filter(pk=obj_id).first()
        elif obj_type == 'subcategory':
            obj = Subcategory.objects.filter(pk=obj_id).first()
        else:
            return JsonResponse({"error": "Invalid obj_type"}, status=400)
            
        if not obj:
            return JsonResponse({"error": "Object not found"}, status=404)
            
        obj.is_active = not obj.is_active
        obj.save(update_fields=['is_active'])
        
        return JsonResponse({"status": "success", "is_active": obj.is_active})

    def changelist_view(self, request, extra_context=None):
        from django.db.models import Prefetch, Count, Q
        from catalog.models.category import Category, Subcategory
        from django.template.response import TemplateResponse
        from django.utils.translation import gettext as _

        search_query = request.GET.get('q', '').strip()
        
        categories = Category.objects.all()
        subcategories = Subcategory.objects.all()

        if search_query:
            sub_matches = subcategories.filter(
                Q(code__icontains=search_query) |
                Q(name_ru__icontains=search_query) |
                Q(name_az__icontains=search_query) |
                Q(name_en__icontains=search_query)
            )
            cat_ids_from_subs = sub_matches.values_list('category_id', flat=True)
            
            categories = categories.filter(
                Q(code__icontains=search_query) |
                Q(name_ru__icontains=search_query) |
                Q(name_az__icontains=search_query) |
                Q(name_en__icontains=search_query) |
                Q(code__in=cat_ids_from_subs)
            )

        # Annotate counts and optimize queries
        categories = categories.annotate(
            places_count=Count('place', distinct=True),
            sub_count=Count('subcategories', distinct=True)
        ).order_by('name_ru')

        sub_qs = Subcategory.objects.annotate(
            places_count=Count('place')
        ).order_by('name_ru')

        categories = categories.prefetch_related(
            Prefetch('subcategories', queryset=sub_qs)
        )

        context = {
            **self.admin_site.each_context(request),
            'title': _('Категории и подкатегории'),
            'categories': categories,
            'search_query': search_query,
            'opts': self.model._meta,
            'has_add_permission': self.has_add_permission(request),
            'has_change_permission': self.has_change_permission(request),
            'app_label': self.model._meta.app_label,
        }
        context.update(extra_context or {})
        return TemplateResponse(request, "admin/catalog/category/change_list.html", context)

    def upload_icon_view(self, request):
        if request.method != "POST":
            return JsonResponse({"error": "Method not allowed"}, status=405)

        uploaded_file = request.FILES.get("file")
        if not uploaded_file:
            return JsonResponse({"error": "No file uploaded"}, status=400)

        try:
            media_url = save_uploaded_category_icon(uploaded_file, request.POST.get("code") or "category-icon")
        except forms.ValidationError as exc:
            return JsonResponse({"error": exc.messages[0]}, status=400)
        except Exception as exc:
            return JsonResponse({"error": f"Failed to save file: {str(exc)}"}, status=500)

        return JsonResponse({"success": True, "url": media_url, "path": media_url})



@admin.register(Subcategory)
class SubcategoryAdmin(admin.ModelAdmin):
    form = SubcategoryAdminForm
    list_display = ("name_ru", "category", "name_az", "name_en")
    list_filter = ("category",)
    search_fields = ("name_ru", "name_az", "name_en")
    ordering = ("category", "name_ru")
    exclude = ("code", "order")

    def has_module_permission(self, request):
        # Скрываем подкатегории из бокового меню, так как они управляются из Категорий
        return False
